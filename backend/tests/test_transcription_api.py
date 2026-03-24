import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import TranscriptionStatus, TranscriptionResult, Utterance

@pytest.fixture
def mock_asr():
    mock = AsyncMock()
    mock.submit.return_value = "asr-job-123"
    mock.get_status.return_value = TranscriptionStatus(id="asr-job-123", status="completed")
    mock.get_result.return_value = TranscriptionResult(
        id="asr-job-123", status="completed",
        utterances=[Utterance(start=0, end=1000, text="Hello", speaker="Speaker 1")],
        text="Hello", language="en",
    )
    return mock

@pytest.mark.asyncio
async def test_transcribe_creates_job(mock_asr):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake", "audio/mpeg")},
        )
        file_id = upload_resp.json()["id"]

        with patch("app.routers.transcription.get_asr_backend", return_value=mock_asr):
            resp = await client.post("/api/transcribe", json={
                "file_id": file_id, "language": "en", "model": "base",
            })

    assert resp.status_code == 200
    assert "id" in resp.json()
    assert resp.json()["status"] == "pending"

@pytest.mark.asyncio
async def test_get_transcriptions_list(mock_asr):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/transcriptions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
