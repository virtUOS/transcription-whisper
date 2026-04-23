import asyncio
import smtplib

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.metrics import (
    inc,
    invitations_created_total,
    invitations_revoked_total,
)
from app.models import (
    InvitationAcceptRequest, InvitationAcceptResponse,
    InvitationCreate, InvitationCreated, InvitationListItem,
    UserInfo,
)
from app.services.email import send_invitation_email, EmailConfigError
from app.services.idp_admin import (
    KeycloakAdminClient, KeycloakAdminError, build_default_client,
)
from app.services.invitations import (
    create_invitation, list_invitations, revoke_invitation,
    resolve_invitation_token,
    DuplicatePendingInvitationError,
    InvitationNotFoundError, InvitationExpiredError,
    InvitationRevokedError, InvitationAlreadyAcceptedError,
)


async def _require_invitation_mode() -> None:
    if not settings.INVITATION_MODE:
        raise HTTPException(status_code=404)


async def _require_admin(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


router = APIRouter(dependencies=[Depends(_require_invitation_mode)])


def _invite_url(token: str) -> str:
    base = settings.APP_PUBLIC_URL.rstrip("/")
    return f"{base}/invite/{token}"


@router.post("/api/invitations", response_model=InvitationCreated, status_code=201)
async def post_invitation(
    req: InvitationCreate,
    admin: UserInfo = Depends(_require_admin),
):
    client = build_default_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Keycloak Admin API not configured")

    # Create DB row first.
    async with get_db() as db:
        try:
            inv = await create_invitation(
                db, email=req.email, created_by=admin.email or admin.id,
            )
        except DuplicatePendingInvitationError as e:
            raise HTTPException(status_code=409, detail=str(e))

    # Pre-create in Keycloak and trigger its own setup-email flow.
    try:
        kc_uid = await client.create_user(email=req.email)
        await client.send_setup_email(
            user_id=kc_uid,
            actions=["UPDATE_PASSWORD", "VERIFY_EMAIL"],
            redirect_uri=settings.APP_PUBLIC_URL.rstrip("/") + "/",
        )
    except KeycloakAdminError as e:
        # Roll back the DB row so admin can retry cleanly.
        async with get_db() as db:
            await db.execute("DELETE FROM invitations WHERE id = ?", (inv["id"],))
            await db.commit()
        raise HTTPException(status_code=503, detail=f"Keycloak error: {e}")

    # Send our own invitation email with the /invite/<token> landing link.
    # SMTP is blocking; run it off the event loop.
    try:
        await asyncio.to_thread(
            send_invitation_email,
            to_email=req.email,
            invite_url=_invite_url(inv["token"]),
        )
    except (EmailConfigError, smtplib.SMTPException, OSError) as e:
        # Roll back the invitation row so admins can retry cleanly.
        async with get_db() as db:
            await db.execute("DELETE FROM invitations WHERE id = ?", (inv["id"],))
            await db.commit()
        raise HTTPException(status_code=503, detail=f"Invitation email failed: {e}")

    inc(invitations_created_total)
    return InvitationCreated(**inv)


@router.get("/api/invitations", response_model=list[InvitationListItem])
async def get_invitations(_admin: UserInfo = Depends(_require_admin)):
    async with get_db() as db:
        items = await list_invitations(db)
    return [InvitationListItem(**it) for it in items]


@router.delete("/api/invitations/{invitation_id}", status_code=204)
async def delete_invitation(
    invitation_id: str,
    _admin: UserInfo = Depends(_require_admin),
):
    async with get_db() as db:
        ok = await revoke_invitation(db, invitation_id=invitation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Invitation not found")
    inc(invitations_revoked_total)
    return Response(status_code=204)


@router.post("/api/invitations/accept", response_model=InvitationAcceptResponse)
async def post_accept(req: InvitationAcceptRequest):
    # This endpoint is public — the invitee is not yet authenticated.
    async with get_db() as db:
        try:
            await resolve_invitation_token(db, raw_token=req.token)
        except InvitationNotFoundError:
            raise HTTPException(status_code=404, detail="Invitation not found")
        except InvitationExpiredError:
            raise HTTPException(status_code=410, detail="Invitation expired")
        except InvitationRevokedError:
            raise HTTPException(status_code=410, detail="Invitation revoked")
        except InvitationAlreadyAcceptedError:
            raise HTTPException(status_code=410, detail="Invitation already used")

    # Acceptance proper happens on the invitee's first login via the dependency
    # gate in dependencies.py. Here we just point them at Keycloak's account
    # setup page; Keycloak's execute-actions-email flow completes there.
    issuer = settings.KEYCLOAK_ADMIN_URL.rstrip("/")
    realm = settings.KEYCLOAK_TARGET_REALM
    return InvitationAcceptResponse(
        redirect_url=f"{issuer}/realms/{realm}/account",
    )
