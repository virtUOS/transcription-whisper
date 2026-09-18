"""POST /api/refine/{id} persists a partial result; POST /api/refine/{id}/retry
re-runs only the failed ranges and splices the recovered ones back in."""
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models import LLMRefinementResponse, Utterance
from app.routers import refinement as refinement_router

PROVIDER = "app.routers.refinement.get_llm_provider"


def _orig(n=4):
    return [
        {"start": i * 1000, "end": i * 1000 + 500, "text": f"line {i}", "speaker": "S"}
        for i in range(n)
    ]


async def _setup(client, *, refined=None, metadata=None, txn_id="retry-test"):
    upload = await client.post("/api/upload", files={"file": ("t.mp3", b"fake", "audio/mpeg")})
    file_id = upload.json()["id"]
    async with get_db() as db:
        cursor = await db.execute("SELECT user_id FROM files WHERE id = ?", (file_id,))
        user_id = (await cursor.fetchone())[0]
        await db.execute(
            """INSERT INTO transcriptions
               (id, user_id, file_id, asr_backend, status, result_json,
                refined_utterances_json, refinement_metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (txn_id, user_id, file_id, "murmurai", "completed", json.dumps(_orig()),
             json.dumps(refined) if refined is not None else None,
             json.dumps(metadata) if metadata is not None else None),
        )
        await db.commit()
    return txn_id


def _partial_state():
    """Utterances 0-1 refined; 2-3 failed and still hold original text."""
    refined = _orig()
    refined[0]["text"] = "LINE 0"
    refined[1]["text"] = "LINE 1"
    metadata = {
        "changed_indices": [0, 1],
        "changes_summary": "upper-cased first half",
        "context": "meeting notes",
        "llm_provider": "test",
        "llm_model": "m",
        "created_at": "2026-09-18T00:00:00+00:00",
        "failed_ranges": [[2, 4]],
    }
    return refined, metadata


def _provider_returning(texts, failed_ranges=(), summary="merged"):
    provider = AsyncMock()
    provider.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[
            Utterance(start=i * 1000, end=i * 1000 + 500, text=t, speaker="S")
            for i, t in enumerate(texts)
        ],
        changes_summary=summary,
        failed_ranges=list(failed_ranges),
    )
    return provider


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_initial_post_persists_partial_result_with_200():
    provider = _provider_returning(
        ["LINE 0", "LINE 1", "line 2", "line 3"], failed_ranges=[(2, 4)], summary="half done",
    )
    async with _client() as client:
        txn = await _setup(client)
        with patch(PROVIDER, return_value=provider):
            resp = await client.post(f"/api/refine/{txn}")
        assert resp.status_code == 200
        assert resp.json()["metadata"]["failed_ranges"] == [[2, 4]]
        assert resp.json()["metadata"]["changed_indices"] == [0, 1]
        get = await client.get(f"/api/refine/{txn}")
    assert get.json()["metadata"]["failed_ranges"] == [[2, 4]]


@pytest.mark.asyncio
async def test_retry_404_without_refinement():
    async with _client() as client:
        txn = await _setup(client)
        with patch(PROVIDER, return_value=AsyncMock()):
            resp = await client.post(f"/api/refine/{txn}/retry")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_retry_400_when_nothing_failed():
    refined, metadata = _partial_state()
    metadata["failed_ranges"] = []
    async with _client() as client:
        txn = await _setup(client, refined=refined, metadata=metadata)
        with patch(PROVIDER, return_value=AsyncMock()):
            resp = await client.post(f"/api/refine/{txn}/retry")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_retry_splices_recovered_range_and_clears_it():
    refined, metadata = _partial_state()
    # The provider returns a full-length list: outside the retried range as
    # sent, inside it refined. The router must copy only the retried range.
    provider = _provider_returning(["line 0", "line 1", "LINE 2", "LINE 3"], summary="merged summary")
    async with _client() as client:
        txn = await _setup(client, refined=refined, metadata=metadata)
        with patch(PROVIDER, return_value=provider):
            resp = await client.post(f"/api/refine/{txn}/retry")
        assert resp.status_code == 200
        body = resp.json()
        assert [u["text"] for u in body["utterances"]] == ["LINE 0", "LINE 1", "LINE 2", "LINE 3"]
        assert body["metadata"]["failed_ranges"] == []
        assert body["metadata"]["changed_indices"] == [0, 1, 2, 3]
        assert body["metadata"]["changes_summary"] == "merged summary"
        assert body["metadata"]["context"] == "meeting notes"
        get = await client.get(f"/api/refine/{txn}")
        assert get.json()["metadata"]["failed_ranges"] == []

    kwargs = provider.generate_refinement.call_args.kwargs
    assert kwargs["ranges"] == [(2, 4)]
    assert kwargs["context"] == "meeting notes"
    assert kwargs["previous_summary"] == "upper-cased first half"


@pytest.mark.asyncio
async def test_retry_keeps_a_range_that_fails_again():
    refined, metadata = _partial_state()
    provider = _provider_returning(
        ["line 0", "line 1", "line 2", "line 3"],
        failed_ranges=[(2, 4)], summary="upper-cased first half",
    )
    async with _client() as client:
        txn = await _setup(client, refined=refined, metadata=metadata)
        with patch(PROVIDER, return_value=provider):
            resp = await client.post(f"/api/refine/{txn}/retry")
    assert resp.status_code == 200
    body = resp.json()
    assert [u["text"] for u in body["utterances"]] == ["LINE 0", "LINE 1", "line 2", "line 3"]
    assert body["metadata"]["failed_ranges"] == [[2, 4]]
    assert body["metadata"]["changed_indices"] == [0, 1]


@pytest.mark.asyncio
async def test_retry_500_leaves_the_partial_untouched_and_releases_the_guard():
    refined, metadata = _partial_state()
    provider = AsyncMock()
    provider.generate_refinement.side_effect = RuntimeError("boom")
    async with _client() as client:
        txn = await _setup(client, refined=refined, metadata=metadata)
        with patch(PROVIDER, return_value=provider):
            resp = await client.post(f"/api/refine/{txn}/retry")
        assert resp.status_code == 500
        get = await client.get(f"/api/refine/{txn}")
        assert get.status_code == 200
        assert get.json()["metadata"]["failed_ranges"] == [[2, 4]]
        assert [u["text"] for u in get.json()["utterances"]] == ["LINE 0", "LINE 1", "line 2", "line 3"]
    assert txn not in refinement_router._retries_in_flight


@pytest.mark.asyncio
async def test_concurrent_retry_is_rejected_with_409():
    refined, metadata = _partial_state()
    async with _client() as client:
        txn = await _setup(client, refined=refined, metadata=metadata)
        refinement_router._retries_in_flight.add(txn)
        try:
            with patch(PROVIDER, return_value=AsyncMock()):
                resp = await client.post(f"/api/refine/{txn}/retry")
        finally:
            refinement_router._retries_in_flight.discard(txn)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_retry_409_when_transcript_was_edited_since_the_partial_was_saved():
    """An edit to the original transcript (rows deleted via the editable view)
    between the partial run and the retry must not let the splice shrink the
    stored refined list. The stored partial stays exactly as it was."""
    refined, metadata = _partial_state()
    # The provider will be handed the *edited* 3-utterance transcript and, being
    # full-length relative to its input, returns 3 utterances.
    provider = _provider_returning(["line 0", "line 1", "LINE 2"])
    async with _client() as client:
        txn = await _setup(client, refined=refined, metadata=metadata)
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET result_json = ? WHERE id = ?",
                (json.dumps(_orig()[:3]), txn),
            )
            await db.commit()
        with patch(PROVIDER, return_value=provider):
            resp = await client.post(f"/api/refine/{txn}/retry")
        assert resp.status_code == 409
        get = await client.get(f"/api/refine/{txn}")
    assert get.status_code == 200
    assert [u["text"] for u in get.json()["utterances"]] == ["LINE 0", "LINE 1", "line 2", "line 3"]
    assert get.json()["metadata"]["failed_ranges"] == [[2, 4]]
    assert txn not in refinement_router._retries_in_flight


@pytest.mark.asyncio
async def test_retry_does_not_resurrect_a_refinement_deleted_mid_flight():
    refined, metadata = _partial_state()

    async def delete_then_return(*args, **kwargs):
        async with get_db() as db:
            await db.execute(
                """UPDATE transcriptions
                   SET refined_utterances_json = NULL, refinement_metadata_json = NULL
                   WHERE id = ?""",
                ("retry-test",),
            )
            await db.commit()
        return LLMRefinementResponse(
            utterances=[
                Utterance(start=i * 1000, end=i * 1000 + 500, text=t, speaker="S")
                for i, t in enumerate(["line 0", "line 1", "LINE 2", "LINE 3"])
            ],
            changes_summary="x",
            failed_ranges=[],
        )

    provider = AsyncMock()
    provider.generate_refinement.side_effect = delete_then_return
    async with _client() as client:
        txn = await _setup(client, refined=refined, metadata=metadata)
        with patch(PROVIDER, return_value=provider):
            resp = await client.post(f"/api/refine/{txn}/retry")
        assert resp.status_code == 200
        get = await client.get(f"/api/refine/{txn}")
    assert get.status_code == 404
