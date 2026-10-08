"""An analysis whose reply reached the output cap must tell the user so.

The router re-raised every failure, so the browser got a bare 500 and showed
"Internal Server Error" after a wait of minutes. On 2026-10-08 a user retried
such an analysis, which could not help, and gave up. A reply that reached the
cap is a property of the request (4 of 4 attempts hit it), so it gets its own
status the frontend can explain, and the placeholder row is still removed so
a narrower prompt can be tried straight away.
"""
import json

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.llm.base import OutputLimitExceeded


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
async def test_output_limit_is_a_422_with_an_explanation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _setup(client, "test-analysis-output-limit")
        provider = AsyncMock()
        provider.generate_summary.side_effect = OutputLimitExceeded("cap")
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            resp = await client.post("/api/analysis/test-analysis-output-limit", json={"template": "summary"})
    assert resp.status_code == 422
    assert "output limit" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_output_limit_removes_the_placeholder_so_the_user_can_try_again():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _setup(client, "test-analysis-output-limit-retry")
        provider = AsyncMock()
        provider.generate_summary.side_effect = OutputLimitExceeded("cap")
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            await client.post("/api/analysis/test-analysis-output-limit-retry", json={"template": "summary"})
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute(
            "SELECT COUNT(*) FROM analyses WHERE transcription_id = ?", ("test-analysis-output-limit-retry",),
        )).fetchone()
    assert row[0] == 0
