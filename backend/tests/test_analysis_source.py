import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


async def _setup(client, *, txn_id="test-analysis-src", with_refined=False):
    upload_resp = await client.post("/api/upload", files={"file": ("t.mp3", b"x", "audio/mpeg")})
    file_id = upload_resp.json()["id"]
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute("SELECT user_id FROM files WHERE id = ?", (file_id,))).fetchone()
        user_id = row[0]
        original = json.dumps([{"start": 0, "end": 1000, "text": "original text", "speaker": "A"}])
        refined = json.dumps([{"start": 0, "end": 1000, "text": "refined text", "speaker": "A"}]) if with_refined else None
        await db.execute(
            """INSERT INTO transcriptions
               (id, user_id, file_id, asr_backend, status, language, result_json, refined_utterances_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (txn_id, user_id, file_id, "murmurai", "completed", "en", original, refined),
        )
        await db.commit()
    return txn_id, user_id


def _summary_response():
    from app.models import SummaryResult
    return SummaryResult(summary="ok", chapters=[], chapter_hints=None, language="en")


@pytest.mark.asyncio
async def test_analysis_captures_refined_source_by_default():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, with_refined=True)
        provider = AsyncMock()
        provider.generate_summary.return_value = _summary_response()
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            resp = await client.post(f"/api/analysis/{txn_id}", json={"template": "summary"})
        called_args = provider.generate_summary.call_args
        assert "refined text" in called_args.args[0]
    assert resp.status_code == 200
    assert resp.json()["source"] == "refined"
    assert resp.json()["stale"] is False


@pytest.mark.asyncio
async def test_analysis_uses_original_when_explicitly_requested():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, txn_id="test-analysis-orig", with_refined=True)
        provider = AsyncMock()
        provider.generate_summary.return_value = _summary_response()
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            resp = await client.post(f"/api/analysis/{txn_id}", json={"template": "summary", "source": "original"})
        called_args = provider.generate_summary.call_args
        assert "original text" in called_args.args[0]
    assert resp.json()["source"] == "original"


@pytest.mark.asyncio
async def test_analysis_explicit_refined_without_refinement_returns_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, txn_id="test-analysis-400", with_refined=False)
        provider = AsyncMock()
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            resp = await client.post(f"/api/analysis/{txn_id}", json={"template": "summary", "source": "refined"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_analysis_reports_stale_when_source_edited():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, txn_id="test-analysis-stale", with_refined=False)
        provider = AsyncMock()
        provider.generate_summary.return_value = _summary_response()
        with patch("app.routers.analysis.get_llm_provider", return_value=provider):
            post_resp = await client.post(f"/api/analysis/{txn_id}", json={"template": "summary"})
        analysis_id = post_resp.json()["id"]

        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET result_json = ? WHERE id = ?",
                (json.dumps([{"start": 0, "end": 1000, "text": "EDITED", "speaker": "A"}]), txn_id),
            )
            await db.commit()

        get_resp = await client.get(f"/api/analysis/{txn_id}/{analysis_id}")
    assert get_resp.json()["stale"] is True
