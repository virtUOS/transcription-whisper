import pytest
import app.config as config_module
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db
from app.models import UserInfo
from app.services.api_tokens import (
    create_token,
    list_tokens,
    revoke_token,
    resolve_token,
    touch_last_used,
    cleanup_stale_tokens,
    count_active_tokens,
    TokenLimitError,
    DuplicateTokenNameError,
)


async def _seed_user(db, user_id="u1", email="u1@example.com"):
    await db.execute("INSERT INTO users (id, email) VALUES (?, ?)", (user_id, email))
    await db.commit()


@pytest.mark.asyncio
async def test_create_token_returns_raw_and_persists_hash():
    async with get_db() as db:
        await _seed_user(db)
        result = await create_token(db, user_id="u1", name="my-token", expires_in_days=30)

    assert result["token"].startswith("tw_")
    assert result["prefix"] == result["token"][:12]
    assert "token_hash" not in result

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT token_hash FROM api_tokens WHERE id = ?", (result["id"],)
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["token_hash"] != result["token"]


@pytest.mark.asyncio
async def test_create_token_rejects_duplicate_name():
    async with get_db() as db:
        await _seed_user(db)
        await create_token(db, user_id="u1", name="dup-name", expires_in_days=30)
        with pytest.raises(DuplicateTokenNameError):
            await create_token(db, user_id="u1", name="dup-name", expires_in_days=30)


@pytest.mark.asyncio
async def test_create_token_enforces_per_user_cap(monkeypatch):
    monkeypatch.setattr(config_module.settings, "API_TOKEN_MAX_PER_USER", 2)
    async with get_db() as db:
        await _seed_user(db)
        await create_token(db, user_id="u1", name="token-1", expires_in_days=30)
        await create_token(db, user_id="u1", name="token-2", expires_in_days=30)
        with pytest.raises(TokenLimitError):
            await create_token(db, user_id="u1", name="token-3", expires_in_days=30)


@pytest.mark.asyncio
async def test_list_tokens_returns_user_tokens_only():
    async with get_db() as db:
        await _seed_user(db, "u1", "u1@example.com")
        await _seed_user(db, "u2", "u2@example.com")
        await create_token(db, user_id="u1", name="u1-token", expires_in_days=30)
        await create_token(db, user_id="u2", name="u2-token", expires_in_days=30)

        tokens = await list_tokens(db, user_id="u1")

    assert len(tokens) == 1
    assert tokens[0]["name"] == "u1-token"
    assert "token" not in tokens[0]
    assert "token_hash" not in tokens[0]


@pytest.mark.asyncio
async def test_revoke_token_sets_revoked_at_and_blocks_reuse():
    async with get_db() as db:
        await _seed_user(db)
        t = await create_token(db, user_id="u1", name="to-revoke", expires_in_days=30)
        revoked = await revoke_token(db, user_id="u1", token_id=t["id"])
        assert revoked is True

        result = await resolve_token(db, raw_token=t["token"])
        assert result is None


@pytest.mark.asyncio
async def test_revoke_token_returns_false_for_other_user():
    async with get_db() as db:
        await _seed_user(db, "u1", "u1@example.com")
        await _seed_user(db, "u2", "u2@example.com")
        t = await create_token(db, user_id="u1", name="u1-token", expires_in_days=30)
        revoked = await revoke_token(db, user_id="u2", token_id=t["id"])
        assert revoked is False


@pytest.mark.asyncio
async def test_resolve_token_returns_user_for_valid_token():
    async with get_db() as db:
        await _seed_user(db, "u1", "u1@example.com")
        t = await create_token(db, user_id="u1", name="valid-token", expires_in_days=30)

        result = await resolve_token(db, raw_token=t["token"])
        assert result is not None
        user, token_id = result
        assert isinstance(user, UserInfo)
        assert user.id == "u1"
        assert user.email == "u1@example.com"
        assert token_id == t["id"]


@pytest.mark.asyncio
async def test_resolve_token_rejects_expired():
    async with get_db() as db:
        await _seed_user(db)
        t = await create_token(db, user_id="u1", name="will-expire", expires_in_days=30)
        await db.execute(
            "UPDATE api_tokens SET expires_at = ? WHERE id = ?",
            ("2000-01-01 00:00:00", t["id"]),
        )
        await db.commit()

        result = await resolve_token(db, raw_token=t["token"])
        assert result is None


@pytest.mark.asyncio
async def test_resolve_token_rejects_unknown_token():
    async with get_db() as db:
        result = await resolve_token(db, raw_token="tw_totallyfake")
        assert result is None


@pytest.mark.asyncio
async def test_cleanup_stale_tokens_removes_old_revoked_and_expired():
    from datetime import datetime, timedelta, timezone

    async with get_db() as db:
        await _seed_user(db)

        # Token 1: revoked 40 days ago
        t1 = await create_token(db, user_id="u1", name="old-revoked", expires_in_days=None)
        revoked_40_days_ago = (
            datetime.now(timezone.utc) - timedelta(days=40)
        ).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            "UPDATE api_tokens SET revoked_at = ? WHERE id = ?",
            (revoked_40_days_ago, t1["id"]),
        )

        # Token 2: expired 100 days ago
        t2 = await create_token(db, user_id="u1", name="old-expired", expires_in_days=None)
        expired_100_days_ago = (
            datetime.now(timezone.utc) - timedelta(days=100)
        ).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            "UPDATE api_tokens SET expires_at = ? WHERE id = ?",
            (expired_100_days_ago, t2["id"]),
        )

        # Token 3: active
        await create_token(db, user_id="u1", name="still-active", expires_in_days=30)

        await db.commit()

        deleted = await cleanup_stale_tokens(db)

        cursor = await db.execute("SELECT name FROM api_tokens")
        rows = await cursor.fetchall()
        remaining_names = {r["name"] for r in rows}
    assert deleted == 2
    assert remaining_names == {"still-active"}


@pytest.mark.asyncio
async def test_create_token_cap_ignores_expired_tokens(monkeypatch):
    monkeypatch.setattr(config_module.settings, "API_TOKEN_MAX_PER_USER", 2)
    async with get_db() as db:
        await _seed_user(db)
        # Two active tokens → at cap
        await create_token(db, user_id="u1", name="a", expires_in_days=None)
        b = await create_token(db, user_id="u1", name="b", expires_in_days=None)
        # Force one to be expired → no longer "active"
        await db.execute(
            "UPDATE api_tokens SET expires_at = '2000-01-01 00:00:00' WHERE id = ?",
            (b["id"],),
        )
        await db.commit()
        # Should now be allowed — only one "active" token
        result = await create_token(db, user_id="u1", name="c", expires_in_days=None)
    assert result["id"] is not None


@pytest.mark.asyncio
async def test_touch_last_used_updates_timestamp():
    from app.database import get_db
    async with get_db() as db:
        await _seed_user(db)
        t = await create_token(db, user_id="u1", name="touch-test", expires_in_days=None)

        # Fetch initial last_used_at — should be NULL
        cursor = await db.execute("SELECT last_used_at FROM api_tokens WHERE id = ?", (t["id"],))
        row = await cursor.fetchone()
        assert row["last_used_at"] is None

        await touch_last_used(db, token_id=t["id"])

        cursor = await db.execute("SELECT last_used_at FROM api_tokens WHERE id = ?", (t["id"],))
        row = await cursor.fetchone()
    assert row["last_used_at"] is not None


@pytest.mark.asyncio
async def test_create_token_endpoint_returns_raw_token_once(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post("/api/tokens", json={"name": "my-cli", "expires_in_days": 30})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["token"].startswith("tw_")
        assert data["prefix"] == data["token"][:12]

        r2 = await c.get("/api/tokens")
        assert r2.status_code == 200
        items = r2.json()
        assert len(items) == 1
        assert "token" not in items[0]


@pytest.mark.asyncio
async def test_create_token_rejects_empty_name(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post("/api/tokens", json={"name": "   ", "expires_in_days": None})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_token_duplicate_name_returns_409(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post("/api/tokens", json={"name": "dup", "expires_in_days": None})
        r = await c.post("/api/tokens", json={"name": "dup", "expires_in_days": None})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_token_over_cap_returns_429(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", True)
    monkeypatch.setattr(config_module.settings, "API_TOKEN_MAX_PER_USER", 1)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post("/api/tokens", json={"name": "a", "expires_in_days": None})
        r = await c.post("/api/tokens", json={"name": "b", "expires_in_days": None})
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_revoke_token_returns_204_and_blocks_reuse(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        created = (await c.post("/api/tokens", json={"name": "r", "expires_in_days": None})).json()
        r = await c.delete(f"/api/tokens/{created['id']}")
        assert r.status_code == 204
        r2 = await c.get("/api/tokens", headers={"Authorization": f"Bearer {created['token']}"})
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_routes_absent_when_flag_off(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", False)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/tokens")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_tokens_user_isolated(monkeypatch):
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    monkeypatch.setattr(config_module.settings, "DEV_MODE", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post("/api/tokens", json={"name": "dev-t", "expires_in_days": None})
        await c.post(
            "/api/tokens",
            headers={"X-Auth-Request-User": "alice"},
            json={"name": "alice-t", "expires_in_days": None},
        )
        items = (await c.get("/api/tokens")).json()
    names = {i["name"] for i in items}
    assert names == {"dev-t"}
