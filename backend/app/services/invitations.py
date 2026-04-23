import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from aiosqlite import Connection

from app.config import settings


class DuplicatePendingInvitationError(Exception):
    """Raised when a pending invitation already exists for this email."""


class InvitationNotFoundError(Exception):
    """Raised when no invitation matches the given token or id."""


class InvitationExpiredError(Exception):
    """Raised when the invitation has passed its expires_at."""


class InvitationRevokedError(Exception):
    """Raised when the invitation was revoked."""


class InvitationAlreadyAcceptedError(Exception):
    """Raised when the invitation has already been accepted."""


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def create_invitation(
    db: Connection, *, email: str, created_by: str,
) -> dict:
    """Create a new invitation.

    Raises DuplicatePendingInvitationError if a pending, non-expired invitation
    for this email already exists.
    Returns dict with: id, email, token (raw), status, created_at, expires_at,
    created_by, accepted_at (None).
    """
    email_norm = _normalize_email(email)
    now_dt = datetime.now(timezone.utc)
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (now_dt + timedelta(days=settings.INVITATION_EXPIRY_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor = await db.execute(
        "SELECT id FROM invitations WHERE email = ? AND status = 'pending' AND expires_at > ?",
        (email_norm, now),
    )
    if await cursor.fetchone() is not None:
        raise DuplicatePendingInvitationError(
            f"A pending invitation already exists for {email_norm}"
        )

    raw_token = "tw_inv_" + secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    inv_id = str(uuid.uuid4())

    await db.execute(
        """
        INSERT INTO invitations
            (id, email, token_hash, created_by, created_at, expires_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
        (inv_id, email_norm, token_hash, created_by, now, expires_at),
    )
    await db.commit()

    return {
        "id": inv_id,
        "email": email_norm,
        "token": raw_token,
        "status": "pending",
        "created_at": now,
        "expires_at": expires_at,
        "created_by": created_by,
        "accepted_at": None,
    }


async def list_invitations(db: Connection) -> list[dict]:
    cursor = await db.execute(
        """
        SELECT id, email, status, created_at, expires_at, created_by, accepted_at
        FROM invitations
        ORDER BY created_at DESC
        """
    )
    rows = await cursor.fetchall()
    return [
        {
            "id": row["id"],
            "email": row["email"],
            "status": row["status"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "created_by": row["created_by"],
            "accepted_at": row["accepted_at"],
        }
        for row in rows
    ]


async def revoke_invitation(db: Connection, *, invitation_id: str) -> bool:
    cursor = await db.execute(
        "UPDATE invitations SET status = 'revoked' WHERE id = ? AND status = 'pending'",
        (invitation_id,),
    )
    await db.commit()
    return cursor.rowcount > 0


async def resolve_invitation_token(db: Connection, *, raw_token: str) -> dict:
    token_hash = _hash_token(raw_token)
    cursor = await db.execute(
        "SELECT id, email, status, expires_at FROM invitations WHERE token_hash = ?",
        (token_hash,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise InvitationNotFoundError("No invitation for this token")
    if row["status"] == "revoked":
        raise InvitationRevokedError("Invitation has been revoked")
    if row["status"] == "accepted":
        raise InvitationAlreadyAcceptedError("Invitation already used")
    now = _now_str()
    if row["expires_at"] <= now:
        raise InvitationExpiredError("Invitation has expired")
    return {
        "id": row["id"],
        "email": row["email"],
        "status": row["status"],
        "expires_at": row["expires_at"],
    }


async def accept_invitation(
    db: Connection, *, raw_token: str, user_id: str,
) -> dict:
    """Mark the invitation accepted. Returns the invitation row."""
    inv = await resolve_invitation_token(db, raw_token=raw_token)
    now = _now_str()
    await db.execute(
        """
        UPDATE invitations
        SET status = 'accepted', accepted_at = ?, accepted_by_user_id = ?
        WHERE id = ?
        """,
        (now, user_id, inv["id"]),
    )
    await db.commit()
    return inv


async def expire_pending_invitations(db: Connection) -> int:
    now = _now_str()
    cursor = await db.execute(
        "UPDATE invitations SET status = 'expired' WHERE status = 'pending' AND expires_at <= ?",
        (now,),
    )
    await db.commit()
    return cursor.rowcount


async def cleanup_old_invitations(db: Connection) -> int:
    """Hard-delete terminal rows (expired|revoked|accepted) older than 30 days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    cursor = await db.execute(
        """
        DELETE FROM invitations
        WHERE status IN ('expired', 'revoked', 'accepted')
          AND created_at < ?
        """,
        (cutoff,),
    )
    await db.commit()
    return cursor.rowcount


async def email_has_accepted_invitation(db: Connection, *, email: str) -> bool:
    email_norm = _normalize_email(email)
    cursor = await db.execute(
        "SELECT 1 FROM invitations WHERE email = ? AND status = 'accepted' LIMIT 1",
        (email_norm,),
    )
    return await cursor.fetchone() is not None
