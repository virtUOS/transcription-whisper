import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


async def _setup(client, *, txn_id="test-translate", with_refined=False):
    upload_resp = await client.post("/api/upload", files={"file": ("t.mp3", b"x", "audio/mpeg")})
    file_id = upload_resp.json()["id"]
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute("SELECT user_id FROM files WHERE id = ?", (file_id,))).fetchone()
        user_id = row[0]
        original = json.dumps([
            {"start": 0, "end": 1000, "text": "Hallo Welt", "speaker": "A"},
            {"start": 1000, "end": 2000, "text": "Wie geht es dir", "speaker": "B"},
        ])
        refined = json.dumps([
            {"start": 0, "end": 1000, "text": "Hallo, Welt.", "speaker": "A"},
            {"start": 1000, "end": 2000, "text": "Wie geht es dir?", "speaker": "B"},
        ]) if with_refined else None
        await db.execute(
            """INSERT INTO transcriptions
               (id, user_id, file_id, asr_backend, status, result_json, refined_utterances_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (txn_id, user_id, file_id, "murmurai", "completed", original, refined),
        )
        await db.commit()
    return txn_id, user_id


def _translated(texts):
    return [{"start": i * 1000, "end": (i + 1) * 1000, "text": t, "speaker": None}
            for i, t in enumerate(texts)]


@pytest.mark.asyncio
async def test_translate_defaults_to_refined_when_available():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, with_refined=True)
        translated = _translated(["Hello, world.", "How are you?"])
        with patch("app.routers.translation.get_llm_provider", return_value=AsyncMock()), \
             patch("app.routers.translation._call_llm_translation", return_value=translated):
            resp = await client.post(f"/api/translate/{txn_id}", json={"target_language": "en"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "refined"
    assert data["source_available"] is True
    assert data["stale"] is False
    assert data["source_hash"] is not None


@pytest.mark.asyncio
async def test_translate_defaults_to_original_without_refinement():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, txn_id="test-translate-orig", with_refined=False)
        translated = _translated(["Hello world", "How are you"])
        with patch("app.routers.translation.get_llm_provider", return_value=AsyncMock()), \
             patch("app.routers.translation._call_llm_translation", return_value=translated):
            resp = await client.post(f"/api/translate/{txn_id}", json={"target_language": "en"})
    assert resp.json()["source"] == "original"


@pytest.mark.asyncio
async def test_translate_explicit_refined_without_refinement_returns_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, txn_id="test-translate-400", with_refined=False)
        with patch("app.routers.translation.get_llm_provider", return_value=AsyncMock()):
            resp = await client.post(
                f"/api/translate/{txn_id}",
                json={"target_language": "en", "source": "refined"},
            )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_translate_explicit_original_uses_original_even_with_refinement():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, txn_id="test-translate-force-orig", with_refined=True)
        translated = _translated(["Hello world", "How are you"])
        with patch("app.routers.translation.get_llm_provider", return_value=AsyncMock()), \
             patch("app.routers.translation._call_llm_translation", return_value=translated):
            resp = await client.post(
                f"/api/translate/{txn_id}",
                json={"target_language": "en", "source": "original"},
            )
    assert resp.json()["source"] == "original"


@pytest.mark.asyncio
async def test_get_translation_reports_stale_when_source_changes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, user_id = await _setup(client, txn_id="test-translate-stale", with_refined=False)
        translated = _translated(["Hello world", "How are you"])
        with patch("app.routers.translation.get_llm_provider", return_value=AsyncMock()), \
             patch("app.routers.translation._call_llm_translation", return_value=translated):
            await client.post(f"/api/translate/{txn_id}", json={"target_language": "en"})

        # Mutate the original utterances to simulate a post-save edit.
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET result_json = ? WHERE id = ?",
                (json.dumps([
                    {"start": 0, "end": 1000, "text": "Hallo Welt EDITED", "speaker": "A"},
                    {"start": 1000, "end": 2000, "text": "Wie geht es dir", "speaker": "B"},
                ]), txn_id),
            )
            await db.commit()

        resp = await client.get(f"/api/translate/{txn_id}")
    assert resp.status_code == 200
    assert resp.json()["stale"] is True


@pytest.mark.asyncio
async def test_get_translation_reports_source_unavailable_after_refinement_deleted():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id, _ = await _setup(client, txn_id="test-translate-missing", with_refined=True)
        translated = _translated(["Hello, world.", "How are you?"])
        with patch("app.routers.translation.get_llm_provider", return_value=AsyncMock()), \
             patch("app.routers.translation._call_llm_translation", return_value=translated):
            await client.post(f"/api/translate/{txn_id}", json={"target_language": "en"})

        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET refined_utterances_json = NULL WHERE id = ?",
                (txn_id,),
            )
            await db.commit()

        resp = await client.get(f"/api/translate/{txn_id}")
    data = resp.json()
    assert data["source"] == "refined"
    assert data["source_available"] is False
