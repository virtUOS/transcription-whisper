import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db
from app.services.api_tokens import create_token
from app import config as config_module


@pytest.mark.asyncio
async def test_upload_works_with_bearer_token(monkeypatch):
    # Patch both the config module's settings and the dependencies module's
    # captured reference, to survive importlib.reload side-effects from other
    # tests.
    from app import dependencies as dep
    from app.routers import upload as upload_router
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(dep.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", False)  # force token path
    monkeypatch.setattr(dep.settings, "DEV_MODE", False)

    async with get_db() as db:
        await db.execute("INSERT OR IGNORE INTO users (id, email) VALUES ('alice', 'a@x')")
        await db.commit()
        t = await create_token(db, user_id="alice", name="cli", expires_in_days=None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post(
            "/api/upload",
            headers={"Authorization": f"Bearer {t['token']}"},
            files={"file": ("t.mp3", b"fake", "audio/mpeg")},
        )
    assert r.status_code == 200, r.text
    body = r.json()

    async with get_db() as db:
        cursor = await db.execute("SELECT user_id FROM files WHERE id = ?", (body["id"],))
        row = await cursor.fetchone()
    assert row["user_id"] == "alice"
