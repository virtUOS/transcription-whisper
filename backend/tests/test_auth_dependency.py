import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Depends

from app.dependencies import get_current_user
from app.models import UserInfo
from app.database import get_db
from app.services.api_tokens import create_token
from app import config as config_module


def _mini_app() -> FastAPI:
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(user: UserInfo = Depends(get_current_user)):
        return {"id": user.id, "email": user.email}

    return app


@pytest.mark.asyncio
async def test_token_wins_over_headers(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    async with get_db() as db:
        await db.execute("INSERT INTO users (id, email) VALUES ('u1', 'u1@x')")
        await db.commit()
        t = await create_token(db, user_id="u1", name="k", expires_in_days=None)

    transport = ASGITransport(app=_mini_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(
            "/whoami",
            headers={
                "Authorization": f"Bearer {t['token']}",
                "X-Auth-Request-User": "someone-else",
            },
        )
    assert r.status_code == 200
    assert r.json()["id"] == "u1"


@pytest.mark.asyncio
async def test_invalid_token_returns_401_no_fallback(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    transport = ASGITransport(app=_mini_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(
            "/whoami",
            headers={
                "Authorization": "Bearer tw_notvalid",
                "X-Auth-Request-User": "headers-user",
            },
        )
    assert r.status_code == 401
    assert r.headers.get("www-authenticate", "").startswith("Bearer")


@pytest.mark.asyncio
async def test_headers_used_when_no_authorization(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    transport = ASGITransport(app=_mini_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(
            "/whoami",
            headers={"X-Auth-Request-User": "u1", "X-Auth-Request-Email": "u1@x"},
        )
    assert r.status_code == 200
    assert r.json()["id"] == "u1"


@pytest.mark.asyncio
async def test_token_ignored_when_flag_off(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", False)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", False)
    transport = ASGITransport(app=_mini_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/whoami", headers={"Authorization": "Bearer tw_anything"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_non_tw_bearer_falls_through(monkeypatch):
    """Future-compat: `Bearer jwt…` should not be swallowed as an invalid tw token."""
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    transport = ASGITransport(app=_mini_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(
            "/whoami",
            headers={"Authorization": "Bearer eyJ.jwt.token",
                     "X-Auth-Request-User": "u1"},
        )
    assert r.status_code == 200
    assert r.json()["id"] == "u1"
