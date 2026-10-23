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
        # Upload a file first so we have something in the list
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake", "audio/mpeg")},
        )
        file_id = upload_resp.json()["id"]

        with patch("app.routers.transcription.get_asr_backend", return_value=mock_asr):
            await client.post("/api/transcribe", json={
                "file_id": file_id, "language": "en", "model": "base",
            })

        resp = await client.get("/api/transcriptions")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) > 0
    item = items[0]
    assert "expires_at" in item
    assert "archived" in item
    assert item["archived"] is False

@pytest.mark.asyncio
async def test_archive_transcription(mock_asr):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake", "audio/mpeg")},
        )
        file_id = upload_resp.json()["id"]

        with patch("app.routers.transcription.get_asr_backend", return_value=mock_asr):
            transcribe_resp = await client.post("/api/transcribe", json={
                "file_id": file_id, "language": "en", "model": "base",
            })
        transcription_id = transcribe_resp.json()["id"]

        resp = await client.post(f"/api/transcription/{transcription_id}/archive")
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"
        assert "expires_at" in resp.json()

        # Verify list reflects archived state
        list_resp = await client.get("/api/transcriptions")
        items = list_resp.json()
        archived_item = next(i for i in items if i["id"] == transcription_id)
        assert archived_item["archived"] is True

@pytest.mark.asyncio
async def test_archive_nonexistent_transcription():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/transcription/nonexistent-id/archive")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_deleted_during_processing_skips_title(mock_asr):
    """A transcription deleted mid-run must not have its text sent to the LLM."""
    from unittest.mock import MagicMock
    from app.database import get_db
    from app.models import TranscriptionSettings as TranscriptionSettingsModel
    from app.routers.transcription import _run_transcription

    async with get_db() as db:
        await db.execute(
            "INSERT INTO transcriptions (id, asr_backend, status) VALUES (?, ?, ?)",
            ("txn-del", "murmurai", "pending"),
        )
        await db.commit()

    original_result = mock_asr.get_result.return_value

    async def delete_row_then_return(job_id):
        async with get_db() as db:
            await db.execute("DELETE FROM transcriptions WHERE id = ?", ("txn-del",))
            await db.commit()
        return original_result

    mock_asr.get_result.side_effect = delete_row_then_return
    provider = MagicMock()
    provider.generate_title = AsyncMock(return_value="A title")
    req = TranscriptionSettingsModel(file_id="file-1", language="en", model="base")

    with patch("app.routers.transcription.get_asr_backend", return_value=mock_asr), \
         patch("app.services.llm.get_llm_provider", return_value=provider):
        await _run_transcription("txn-del", "/nonexistent/audio.mp3", req, submitted_at=0.0)

    provider.generate_title.assert_not_awaited()
    mock_asr.cleanup.assert_awaited_once_with("asr-job-123")
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM transcriptions WHERE id = ?", ("txn-del",))
        assert await cursor.fetchone() is None
