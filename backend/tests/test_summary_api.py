import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import SummaryResult, SummaryChapter


@pytest.mark.asyncio
async def test_summarize_endpoint():
    mock_provider = AsyncMock()
    mock_provider.generate_summary.return_value = SummaryResult(
        summary="Test summary",
        chapters=[SummaryChapter(title="Intro", start_time=0, end_time=60000, summary="Introduction")],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup: upload + fake transcription in DB
        upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
        file_id = upload_resp.json()["id"]

        # Insert a completed transcription directly into DB
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("test-txn", "anonymous", file_id, "murmurai", "completed",
                 json.dumps([{"start": 0, "end": 5000, "text": "Hello world", "speaker": "Speaker 1"}])),
            )
            await db.commit()

        with patch("app.routers.summary.get_llm_provider", return_value=mock_provider):
            resp = await client.post("/api/summarize/test-txn")

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"] == "Test summary"
    assert len(data["chapters"]) == 1
