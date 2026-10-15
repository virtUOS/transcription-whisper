"""The remote ASR copy of a transcript is deleted once the app has its own.

MurmurAI keeps every transcript it produces until a client deletes it, while the
app expires its copy after DEFAULT_EXPIRY_HOURS. Without the cleanup call the
remote copy outlives the user's, indefinitely.
"""
import pytest
from unittest.mock import AsyncMock, patch

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
