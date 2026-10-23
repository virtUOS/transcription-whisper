"""Transcriptions a restart interrupted are failed, and their remote transcripts deleted."""
import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.database import get_db
from app.main import INTERRUPTED_MESSAGE, app, cleanup_remote_jobs, fail_interrupted_transcriptions


@pytest.mark.asyncio
async def test_interrupted_rows_marked_failed():
    async with get_db() as db:
        for tid, status, job in [
            ("t-pending", "pending", None),
            ("t-processing", "processing", "job-1"),
            ("t-completed", "completed", "job-2"),
            ("t-failed", "failed", "job-3"),
        ]:
            await db.execute(
                "INSERT INTO transcriptions (id, status, asr_job_id, error_message) VALUES (?, ?, ?, ?)",
                (tid, status, job, "old error" if status == "failed" else None),
            )
        await db.commit()

    assert await fail_interrupted_transcriptions() == ["job-1"]

    async with get_db() as db:
        cursor = await db.execute("SELECT id, status, error_message FROM transcriptions")
        rows = {r["id"]: (r["status"], r["error_message"]) for r in await cursor.fetchall()}
    assert rows["t-pending"] == ("failed", INTERRUPTED_MESSAGE)
    assert rows["t-processing"] == ("failed", INTERRUPTED_MESSAGE)
    assert rows["t-completed"] == ("completed", None)
    assert rows["t-failed"] == ("failed", "old error")


@pytest.mark.asyncio
async def test_cleanup_remote_jobs_deletes_each_transcript():
    backend = AsyncMock()
    with patch("app.main.get_asr_backend", return_value=backend):
        await cleanup_remote_jobs(["job-1", "job-2"])
    assert [c.args for c in backend.cleanup.await_args_list] == [("job-1",), ("job-2",)]


def test_startup_does_not_wait_for_remote_cleanup():
    release = threading.Event()
    started = threading.Event()

    async def blocked_cleanup(job_id):
        started.set()
        while not release.is_set():
            await asyncio.sleep(0.01)

    backend = MagicMock()
    backend.cleanup = blocked_cleanup
    with patch("app.main.fail_interrupted_transcriptions", AsyncMock(return_value=["job-1"])), \
         patch("app.main.get_asr_backend", return_value=backend):
        try:
            with TestClient(app) as client:
                assert client.get("/api/health").status_code == 200
                assert started.wait(5)
                assert not release.is_set()
        finally:
            release.set()
