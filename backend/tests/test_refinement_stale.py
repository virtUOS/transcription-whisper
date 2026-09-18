"""A refinement made from an older original reports stale, the way translation does.

Editing the original after refining is legitimate (fixing a typo the LLM
missed). Deleting the refinement on every save would throw away minutes of LLM
output for a one-word change, so the refinement stays and the client is told
it predates the current text.
"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models import LLMRefinementResponse, Utterance
from app.services.source_tracking import hash_utterance_texts

PROVIDER = "app.routers.refinement.get_llm_provider"
ORIG = [
    {"start": 0, "end": 1000, "text": "Hallo Welt", "speaker": "A"},
    {"start": 1000, "end": 2000, "text": "Wie geht es dir", "speaker": "B"},
]


async def _setup(client, txn_id="stale-test", metadata=None, refined=None):
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
            (txn_id, user_id, file_id, "murmurai", "completed", json.dumps(ORIG),
             json.dumps(refined) if refined is not None else None,
             json.dumps(metadata) if metadata is not None else None),
        )
        await db.commit()
    return txn_id


def _provider():
    p = AsyncMock()
    p.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[Utterance(**{**u, "text": u["text"] + "."}) for u in ORIG],
        changes_summary="punctuation",
    )
    return p


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _edit_original(txn_id, utterances):
    async with get_db() as db:
        await db.execute(
            "UPDATE transcriptions SET result_json = ? WHERE id = ?",
            (json.dumps(utterances), txn_id),
        )
        await db.commit()


@pytest.mark.asyncio
async def test_fresh_refinement_is_not_stale_and_records_a_source_hash():
    async with _client() as client:
        txn = await _setup(client)
        with patch(PROVIDER, return_value=_provider()):
            resp = await client.post(f"/api/refine/{txn}")
    assert resp.status_code == 200
    assert resp.json()["stale"] is False
    assert resp.json()["metadata"]["source_hash"] == hash_utterance_texts(ORIG)


@pytest.mark.asyncio
async def test_get_reports_stale_after_a_text_edit_to_the_original():
    async with _client() as client:
        txn = await _setup(client)
        with patch(PROVIDER, return_value=_provider()):
            await client.post(f"/api/refine/{txn}")
        await _edit_original(txn, [{**ORIG[0], "text": "Hallo Welt EDITED"}, ORIG[1]])
        resp = await client.get(f"/api/refine/{txn}")
    assert resp.status_code == 200
    assert resp.json()["stale"] is True


@pytest.mark.asyncio
async def test_speaker_and_timestamp_edits_do_not_make_it_stale():
    async with _client() as client:
        txn = await _setup(client)
        with patch(PROVIDER, return_value=_provider()):
            await client.post(f"/api/refine/{txn}")
        await _edit_original(txn, [{**ORIG[0], "speaker": "Renamed", "end": 900}, ORIG[1]])
        resp = await client.get(f"/api/refine/{txn}")
    assert resp.json()["stale"] is False


@pytest.mark.asyncio
async def test_repeated_post_returns_the_existing_refinement_with_its_staleness():
    async with _client() as client:
        txn = await _setup(client)
        with patch(PROVIDER, return_value=_provider()):
            await client.post(f"/api/refine/{txn}")
            await _edit_original(txn, [{**ORIG[0], "text": "Hallo Welt EDITED"}, ORIG[1]])
            resp = await client.post(f"/api/refine/{txn}")
    assert resp.status_code == 200
    assert resp.json()["stale"] is True


@pytest.mark.asyncio
async def test_rows_written_before_source_hash_existed_are_never_stale():
    metadata = {"changed_indices": [], "changes_summary": "x"}
    async with _client() as client:
        txn = await _setup(client, metadata=metadata, refined=ORIG)
        await _edit_original(txn, [{**ORIG[0], "text": "changed"}, ORIG[1]])
        resp = await client.get(f"/api/refine/{txn}")
    assert resp.status_code == 200
    assert resp.json()["stale"] is False


@pytest.mark.asyncio
async def test_retry_reports_stale_when_texts_changed_but_the_count_did_not():
    refined = [dict(u) for u in ORIG]
    refined[0]["text"] = "HALLO WELT"
    metadata = {
        "changed_indices": [0], "changes_summary": "x", "context": None,
        "failed_ranges": [[1, 2]], "source_hash": hash_utterance_texts(ORIG),
    }
    provider = AsyncMock()
    provider.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[Utterance(**ORIG[0]), Utterance(**{**ORIG[1], "text": "WIE GEHT ES EUCH"})],
        changes_summary="x", failed_ranges=[],
    )
    async with _client() as client:
        txn = await _setup(client, metadata=metadata, refined=refined)
        await _edit_original(txn, [ORIG[0], {**ORIG[1], "text": "Wie geht es euch"}])
        with patch(PROVIDER, return_value=provider):
            resp = await client.post(f"/api/refine/{txn}/retry")
    assert resp.status_code == 200
    assert resp.json()["metadata"]["failed_ranges"] == []
    assert resp.json()["stale"] is True
