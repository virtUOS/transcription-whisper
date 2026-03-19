import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import ProtocolResult, ProtocolKeyPoint, ProtocolDecision, ProtocolActionItem


@pytest.mark.asyncio
async def test_protocol_endpoint():
    mock_provider = AsyncMock()
    mock_provider.generate_protocol.return_value = ProtocolResult(
        title="Test Meeting",
        participants=["Alice", "Bob"],
        key_points=[ProtocolKeyPoint(topic="Budget", speaker="Alice", timestamp=5000, content="Approved")],
        decisions=[ProtocolDecision(decision="Ship Friday", timestamp=30000)],
        action_items=[ProtocolActionItem(task="Update docs", assignee="Bob", timestamp=45000)],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
        file_id = upload_resp.json()["id"]

        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("test-txn", "anonymous", file_id, "murmurai", "completed",
                 json.dumps([{"start": 0, "end": 5000, "text": "Hello world", "speaker": "Speaker 1"}])),
            )
            await db.commit()

        with patch("app.routers.protocol.get_llm_provider", return_value=mock_provider):
            resp = await client.post("/api/protocol/test-txn")

    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Meeting"
    assert len(data["participants"]) == 2
    assert len(data["key_points"]) == 1
    assert len(data["decisions"]) == 1
    assert len(data["action_items"]) == 1


@pytest.mark.asyncio
async def test_protocol_endpoint_no_provider():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.routers.protocol.get_llm_provider", return_value=None):
            resp = await client.post("/api/protocol/test-txn")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_protocol_endpoint_returns_cached():
    """Second call should return cached result without calling LLM."""
    mock_provider = AsyncMock()
    mock_provider.generate_protocol.return_value = ProtocolResult(
        title="Test", participants=[], key_points=[], decisions=[], action_items=[],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
        file_id = upload_resp.json()["id"]

        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("test-txn-2", "anonymous", file_id, "murmurai", "completed",
                 json.dumps([{"start": 0, "end": 5000, "text": "Hello", "speaker": "Speaker 1"}])),
            )
            await db.commit()

        with patch("app.routers.protocol.get_llm_provider", return_value=mock_provider):
            resp1 = await client.post("/api/protocol/test-txn-2")
            resp2 = await client.post("/api/protocol/test-txn-2")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # LLM should only be called once
    assert mock_provider.generate_protocol.call_count == 1
