"""The remote ASR copy of a transcript is deleted once the app has its own.

MurmurAI keeps every transcript it produces until a client deletes it, while the
app expires its copy after DEFAULT_EXPIRY_HOURS. Without the cleanup call the
remote copy outlives the user's, indefinitely.
"""
import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.database import get_db
from app.main import app, cleanup_old_files
from app.models import TranscriptionResult, TranscriptionStatus, Utterance
from app.models import TranscriptionSettings as TranscriptionSettingsModel
from app.routers.transcription import _run_transcription


def _backend():
    backend = AsyncMock()
    backend.submit.return_value = "asr-job-123"
    backend.get_status.return_value = TranscriptionStatus(id="asr-job-123", status="completed")
    backend.get_result.return_value = TranscriptionResult(
        id="asr-job-123", status="completed",
        utterances=[Utterance(start=0, end=1000, text="Hello", speaker=None)],
        text="Hello", language="en",
    )
    return backend


async def _run(backend):
    req = TranscriptionSettingsModel(file_id="file-1", language="en", model="base")
    with patch("app.routers.transcription.get_asr_backend", return_value=backend), \
         patch("app.services.llm.get_llm_provider", return_value=None):
        await _run_transcription("txn-1", "/nonexistent/audio.mp3", req, submitted_at=0.0)


@pytest.mark.asyncio
async def test_remote_transcript_deleted_after_result_is_stored():
    backend = _backend()
    await _run(backend)
    backend.cleanup.assert_awaited_once_with("asr-job-123")


@pytest.mark.asyncio
async def test_remote_transcript_deleted_when_job_fails_after_submit():
    """A job that failed or timed out still left a row on the remote side."""
    backend = _backend()
    backend.get_result.side_effect = RuntimeError("asr exploded")
    await _run(backend)
    backend.cleanup.assert_awaited_once_with("asr-job-123")


@pytest.mark.asyncio
async def test_no_remote_delete_when_submit_itself_failed():
    """Nothing was created remotely, so there is nothing to delete."""
    backend = _backend()
    backend.submit.side_effect = RuntimeError("asr unreachable")
    await _run(backend)
    backend.cleanup.assert_not_awaited()


async def _insert(file_id, expires_at, transcriptions):
    """Insert a file and its transcriptions, given as (id, status, asr_job_id)."""
    async with get_db() as db:
        await db.execute("INSERT OR IGNORE INTO users (id, email) VALUES ('dev-user', 'dev@localhost')")
        await db.execute(
            "INSERT INTO files (id, user_id, original_filename, media_type, file_size, expires_at) "
            "VALUES (?, 'dev-user', 'a.mp3', 'mp3', 1, ?)",
            (file_id, expires_at),
        )
        for tid, status, job in transcriptions:
            await db.execute(
                "INSERT INTO transcriptions (id, user_id, file_id, status, asr_job_id) VALUES (?, 'dev-user', ?, ?, ?)",
                (tid, file_id, status, job),
            )
        await db.commit()


@pytest.mark.asyncio
async def test_expiry_deletes_remote_transcripts_of_expired_rows():
    """A remote delete that failed earlier is retried before the row, and its job id, go."""
    await _insert("f-old", "2000-01-01 00:00:00", [("t-old", "completed", "job-old"), ("t-nojob", "failed", None)])
    await _insert("f-new", "2999-01-01 00:00:00", [("t-new", "completed", "job-new")])
    backend = AsyncMock()

    with patch("app.main.get_asr_backend", return_value=backend), \
         patch("app.main.delete_orphaned_media", AsyncMock(return_value=0)), \
         patch("app.main.asyncio.sleep", AsyncMock(side_effect=[None, asyncio.CancelledError()])):
        with pytest.raises(asyncio.CancelledError):
            await cleanup_old_files()

    backend.cleanup.assert_awaited_once_with("job-old")
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM transcriptions")
        assert [row["id"] for row in await cursor.fetchall()] == ["t-new"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status, remote_deletes", [("processing", 1), ("completed", 0)])
async def test_deleting_a_running_job_deletes_its_remote_transcript(status, remote_deletes):
    """A restart before the running job finishes would otherwise leak its remote copy."""
    await _insert("f-1", "2999-01-01 00:00:00", [("t-1", status, "job-1")])
    backend = AsyncMock()

    with patch("app.routers.transcription.get_asr_backend", return_value=backend):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/api/transcription/t-1")

    assert resp.status_code == 200
    assert backend.cleanup.await_count == remote_deletes
    if remote_deletes:
        backend.cleanup.assert_awaited_with("job-1")
