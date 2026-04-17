import asyncio
import uuid
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.main import app
from app.database import get_db
from app.services.api_tokens import create_token
import app.routers.transcription as transcription_module


async def _seed_ws_test_data(user_id: str, transcription_id: str) -> str:
    """Seed user, token, and transcription row; return the raw token string."""
    async with get_db() as db:
        await db.execute(
            "INSERT INTO users (id, email) VALUES (?, ?)",
            (user_id, f"{user_id}@x"),
        )
        await db.commit()
        t = await create_token(db, user_id=user_id, name="ws", expires_in_days=None)
        await db.execute(
            "INSERT INTO transcriptions (id, user_id, status) VALUES (?, ?, 'pending')",
            (transcription_id, user_id),
        )
        await db.commit()
    return t["token"]


def test_ws_accepts_query_param_token(monkeypatch):
    """The WS endpoint should authenticate via ?token=tw_… when flag is on."""
    # Patch the settings object that the transcription router actually holds — not
    # config_module.settings, which may have been replaced by importlib.reload in
    # test_config.py tests that run before this one.
    monkeypatch.setattr(transcription_module.settings, "ENABLE_API_TOKENS", True)
    user_id = str(uuid.uuid4())
    transcription_id = str(uuid.uuid4())

    with TestClient(app) as client:
        # Seed data after lifespan has initialised _db_path
        raw_token = asyncio.run(_seed_ws_test_data(user_id, transcription_id))
        with client.websocket_connect(
            f"/api/ws/status/{transcription_id}?token={raw_token}"
        ) as ws:
            msg = ws.receive_json()
            assert msg["type"] == "status"


def test_ws_rejects_invalid_query_token(monkeypatch):
    monkeypatch.setattr(transcription_module.settings, "ENABLE_API_TOKENS", True)
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(
                "/api/ws/status/anything?token=tw_bad"
            ) as ws:
                ws.receive_json()
    assert exc.value.code == 4001
