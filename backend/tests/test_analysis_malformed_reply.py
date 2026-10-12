"""An analysis whose replies were all unusable must tell the user so.

The router re-raised the failure, so the browser got a bare 500 and showed
"Internal Server Error" (2026-10-12), though analysis_json_chat had written a
message for the user. Each attempt is a fresh draw, so trying again can help,
and the user needs to hear that rather than a server fault.

The frontend explains it in the UI language, keyed on `code` rather than the
status: the proxy in front of the app answers 502 itself when the app is down,
and that must not be reported as a malformed model reply.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.llm.base import MalformedReply
from tests.test_analysis_output_limit import _setup


@pytest.mark.asyncio
async def test_a_malformed_reply_is_a_502_the_frontend_can_identify():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _setup(client, "test-analysis-malformed")
        provider = AsyncMock()
        provider.generate_summary.side_effect = MalformedReply("The language model returned a malformed response.")
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            resp = await client.post("/api/analysis/test-analysis-malformed", json={"template": "summary"})
    assert resp.status_code == 502
    assert resp.json()["code"] == "malformed_reply"
    assert "malformed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_a_malformed_reply_removes_the_placeholder_so_the_user_can_try_again():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _setup(client, "test-analysis-malformed-retry")
        provider = AsyncMock()
        provider.generate_summary.side_effect = MalformedReply("malformed")
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            await client.post("/api/analysis/test-analysis-malformed-retry", json={"template": "summary"})
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute(
            "SELECT COUNT(*) FROM analyses WHERE transcription_id = ?", ("test-analysis-malformed-retry",),
        )).fetchone()
    assert row[0] == 0
