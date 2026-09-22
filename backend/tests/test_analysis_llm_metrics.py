"""The analysis router must count a failed LLM call as a request, like every
other operation. It kept its own inline metrics when llm_requests_total was
changed to count attempts, so a failed analysis bumped errors but not requests.
In production one analysis timeout produced errors=1 / requests=0 and the
failure-ratio alert reported 5.6e7% (errors divided by the clamp floor).
"""
import json

import pytest
from httpx import ASGITransport, AsyncClient
from prometheus_client import REGISTRY
from unittest.mock import AsyncMock, patch

from app.config import settings
from app.main import app


def _value(name):
    return REGISTRY.get_sample_value(
        name, {"provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL, "operation": "analysis"},
    ) or 0.0


async def _setup(client, txn_id):
    upload_resp = await client.post("/api/upload", files={"file": ("t.mp3", b"x", "audio/mpeg")})
    file_id = upload_resp.json()["id"]
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute("SELECT user_id FROM files WHERE id = ?", (file_id,))).fetchone()
        original = json.dumps([{"start": 0, "end": 1000, "text": "original text", "speaker": "A"}])
        await db.execute(
            """INSERT INTO transcriptions
               (id, user_id, file_id, asr_backend, status, language, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (txn_id, row[0], file_id, "murmurai", "completed", "en", original),
        )
        await db.commit()


@pytest.mark.asyncio
async def test_failed_analysis_counts_a_request_and_an_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _setup(client, "test-analysis-metrics-fail")
        provider = AsyncMock()
        provider.generate_summary.side_effect = RuntimeError("Request timed out.")
        r0, e0 = _value("transcription_llm_requests_total"), _value("transcription_llm_errors_total")
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            with pytest.raises(RuntimeError):
                await client.post("/api/analysis/test-analysis-metrics-fail", json={"template": "summary"})
    assert _value("transcription_llm_requests_total") == r0 + 1
    assert _value("transcription_llm_errors_total") == e0 + 1


@pytest.mark.asyncio
async def test_successful_analysis_counts_a_request_and_no_error():
    from app.models import SummaryResult
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _setup(client, "test-analysis-metrics-ok")
        provider = AsyncMock()
        provider.generate_summary.return_value = SummaryResult(summary="ok", chapters=[], chapter_hints=None, language="en")
        r0, e0, d0 = (_value("transcription_llm_requests_total"), _value("transcription_llm_errors_total"),
                      _value("transcription_llm_duration_seconds_count"))
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            resp = await client.post("/api/analysis/test-analysis-metrics-ok", json={"template": "summary"})
    assert resp.status_code == 200
    assert _value("transcription_llm_requests_total") == r0 + 1
    assert _value("transcription_llm_errors_total") == e0
    assert _value("transcription_llm_duration_seconds_count") == d0 + 1
