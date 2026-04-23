import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

import app.config as config_module
from app.main import app
from app.database import get_db


@pytest.fixture(autouse=True)
def _enable_invitation_mode(monkeypatch):
    # Other tests call importlib.reload(config_module), which swaps
    # config_module.settings with a fresh object. Modules that did
    # `from app.config import settings` at import time still hold the old
    # reference, so patch every captured copy that this flow touches.
    from app import dependencies as dep
    from app.routers import invitations as inv_router
    from app.services import invitations as inv_service
    from app.services import email as email_service
    targets = [
        config_module.settings,
        dep.settings,
        inv_router.settings,
        inv_service.settings,
        email_service.settings,
    ]
    overrides = {
        "INVITATION_MODE": True,
        "ADMIN_EMAILS": ["admin@example.com"],
        "KEYCLOAK_ADMIN_URL": "https://kc.example",
        "KEYCLOAK_ADMIN_REALM": "master",
        "KEYCLOAK_TARGET_REALM": "app",
        "KEYCLOAK_ADMIN_CLIENT_ID": "admin-cli",
        "KEYCLOAK_ADMIN_CLIENT_SECRET": "s",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_FROM": "noreply@example.com",
        "APP_PUBLIC_URL": "https://app.example.com",
    }
    seen: set[int] = set()
    for tgt in targets:
        if id(tgt) in seen:
            continue
        seen.add(id(tgt))
        for k, v in overrides.items():
            monkeypatch.setattr(tgt, k, v)


def _admin_headers():
    return {
        "X-Auth-Request-User": "sub-admin",
        "X-Auth-Request-Email": "admin@example.com",
    }


@pytest.mark.asyncio
async def test_create_invitation_requires_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.post(
            "/api/invitations",
            json={"email": "new@example.com"},
            headers={
                "X-Auth-Request-User": "sub-notadmin",
                "X-Auth-Request-Email": "notadmin@example.com",
            },
        )
    # Non-admin in invitation mode with no accepted invite → 403 from the gate
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_invitation_happy_path():
    with patch(
        "app.routers.invitations.KeycloakAdminClient.create_user",
        new=AsyncMock(return_value="kc-uuid-1"),
    ), patch(
        "app.routers.invitations.KeycloakAdminClient.send_setup_email",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.routers.invitations.send_invitation_email",
        return_value=None,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            resp = await c.post(
                "/api/invitations",
                json={"email": "new@example.com"},
                headers=_admin_headers(),
            )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert body["status"] == "pending"
    assert body["token"].startswith("tw_inv_")


@pytest.mark.asyncio
async def test_list_invitations_requires_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.get(
            "/api/invitations",
            headers={
                "X-Auth-Request-User": "sub-notadmin",
                "X-Auth-Request-Email": "notadmin@example.com",
            },
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_invitations_returns_list_for_admin():
    from app.services.invitations import create_invitation
    async with get_db() as db:
        await create_invitation(db, email="one@example.com", created_by="admin@example.com")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.get("/api/invitations", headers=_admin_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert any(item["email"] == "one@example.com" for item in body)


@pytest.mark.asyncio
async def test_revoke_invitation_marks_revoked():
    from app.services.invitations import create_invitation
    async with get_db() as db:
        inv = await create_invitation(
            db, email="victim@example.com", created_by="admin@example.com",
        )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.delete(
            f"/api/invitations/{inv['id']}",
            headers=_admin_headers(),
        )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_revoke_invitation_unknown_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.delete(
            "/api/invitations/nonexistent",
            headers=_admin_headers(),
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_accept_invitation_unknown_token_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.post(
            "/api/invitations/accept",
            json={"token": "tw_inv_nothing"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_accept_invitation_expired_returns_410():
    from datetime import datetime, timezone, timedelta
    from app.services.invitations import create_invitation
    async with get_db() as db:
        inv = await create_invitation(
            db, email="e@example.com", created_by="admin@example.com",
        )
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute("UPDATE invitations SET expires_at = ? WHERE id = ?", (past, inv["id"]))
        await db.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.post("/api/invitations/accept", json={"token": inv["token"]})
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_accept_invitation_revoked_returns_410():
    from app.services.invitations import create_invitation, revoke_invitation
    async with get_db() as db:
        inv = await create_invitation(
            db, email="rv@example.com", created_by="admin@example.com",
        )
        await revoke_invitation(db, invitation_id=inv["id"])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.post("/api/invitations/accept", json={"token": inv["token"]})
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_accept_invitation_valid_returns_redirect_url():
    from app.services.invitations import create_invitation
    async with get_db() as db:
        inv = await create_invitation(
            db, email="valid@example.com", created_by="admin@example.com",
        )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        resp = await c.post("/api/invitations/accept", json={"token": inv["token"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "redirect_url" in body
    assert body["redirect_url"].startswith("https://kc.example")


@pytest.mark.asyncio
async def test_create_invitation_duplicate_returns_409():
    from app.services.invitations import create_invitation
    async with get_db() as db:
        await create_invitation(db, email="dup@example.com", created_by="admin@example.com")
    with patch(
        "app.routers.invitations.KeycloakAdminClient.create_user",
        new=AsyncMock(return_value="kc-uuid-dup"),
    ), patch(
        "app.routers.invitations.KeycloakAdminClient.send_setup_email",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.routers.invitations.send_invitation_email",
        return_value=None,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            resp = await c.post(
                "/api/invitations",
                json={"email": "dup@example.com"},
                headers=_admin_headers(),
            )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_smtp_failure_rolls_back_invitation():
    import smtplib
    with patch(
        "app.routers.invitations.KeycloakAdminClient.create_user",
        new=AsyncMock(return_value="kc-uuid-smtp"),
    ), patch(
        "app.routers.invitations.KeycloakAdminClient.send_setup_email",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.routers.invitations.send_invitation_email",
        side_effect=smtplib.SMTPException("boom"),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            resp = await c.post(
                "/api/invitations",
                json={"email": "smtpfail@example.com"},
                headers=_admin_headers(),
            )
    assert resp.status_code == 503
    # DB row must have been rolled back so a retry would not hit 409.
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM invitations WHERE email = ?", ("smtpfail@example.com",)
        )
        assert await cursor.fetchone() is None
