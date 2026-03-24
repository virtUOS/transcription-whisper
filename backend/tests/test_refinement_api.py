import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import LLMRefinementResponse, Utterance
from app.database import get_db


@pytest.mark.asyncio
async def test_refinement_columns_exist():
    """Verify the transcriptions table has refinement columns."""
    async with get_db() as db:
        cursor = await db.execute("PRAGMA table_info(transcriptions)")
        columns = {row[1] for row in await cursor.fetchall()}
    assert "refined_utterances_json" in columns
    assert "refinement_metadata_json" in columns


async def _setup_transcription(client, txn_id="test-refine"):
    """Helper: upload file + insert completed transcription."""
    upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
    file_id = upload_resp.json()["id"]
    from app.database import get_db
    async with get_db() as db:
        await db.execute(
            """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (txn_id, "anonymous", file_id, "murmurai", "completed",
             json.dumps([
                 {"start": 0, "end": 5000, "text": "Hello world", "speaker": "Speaker 1"},
                 {"start": 5000, "end": 10000, "text": "um how are you", "speaker": "Speaker 2"},
             ])),
        )
        await db.commit()
    return txn_id


@pytest.mark.asyncio
async def test_refine_endpoint():
    mock_provider = AsyncMock()
    mock_provider.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[
            Utterance(start=0, end=5000, text="Hello, world.", speaker="Speaker 1"),
            Utterance(start=5000, end=10000, text="How are you?", speaker="Speaker 2"),
        ],
        changes_summary="Fixed 1 punctuation error, removed 1 filler word",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id = await _setup_transcription(client)
        with patch("app.routers.refinement.get_llm_provider", return_value=mock_provider):
            resp = await client.post(f"/api/refine/{txn_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["utterances"]) == 2
    assert data["utterances"][0]["text"] == "Hello, world."
    assert data["metadata"]["changed_indices"] == [0, 1]
    assert "punctuation" in data["metadata"]["changes_summary"]


@pytest.mark.asyncio
async def test_refine_with_context():
    mock_provider = AsyncMock()
    mock_provider.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[
            Utterance(start=0, end=5000, text="Hello, world.", speaker="Speaker 1"),
            Utterance(start=5000, end=10000, text="How are you?", speaker="Speaker 2"),
        ],
        changes_summary="Fixed punctuation",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id = await _setup_transcription(client, "test-refine-ctx")
        with patch("app.routers.refinement.get_llm_provider", return_value=mock_provider):
            resp = await client.post(f"/api/refine/{txn_id}", json={"context": "CS lecture"})

    assert resp.status_code == 200
    assert resp.json()["metadata"]["context"] == "CS lecture"
    mock_provider.generate_refinement.assert_called_once()


@pytest.mark.asyncio
async def test_refine_returns_cached():
    mock_provider = AsyncMock()
    mock_provider.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[Utterance(start=0, end=5000, text="Cached.", speaker="Speaker 1"),
                    Utterance(start=5000, end=10000, text="Result.", speaker="Speaker 2")],
        changes_summary="Fixed punctuation",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id = await _setup_transcription(client, "test-refine-cache")
        with patch("app.routers.refinement.get_llm_provider", return_value=mock_provider):
            resp1 = await client.post(f"/api/refine/{txn_id}")
            resp2 = await client.post(f"/api/refine/{txn_id}")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert mock_provider.generate_refinement.call_count == 1


@pytest.mark.asyncio
async def test_refine_no_provider_returns_503():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id = await _setup_transcription(client, "test-refine-503")
        with patch("app.routers.refinement.get_llm_provider", return_value=None):
            resp = await client.post(f"/api/refine/{txn_id}")

    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_get_refinement():
    mock_provider = AsyncMock()
    mock_provider.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[Utterance(start=0, end=5000, text="Hello.", speaker="Speaker 1"),
                    Utterance(start=5000, end=10000, text="Hi.", speaker="Speaker 2")],
        changes_summary="Fixed punctuation",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id = await _setup_transcription(client, "test-get-refine")
        with patch("app.routers.refinement.get_llm_provider", return_value=mock_provider):
            await client.post(f"/api/refine/{txn_id}")
            resp = await client.get(f"/api/refine/{txn_id}")

    assert resp.status_code == 200
    assert len(resp.json()["utterances"]) == 2


@pytest.mark.asyncio
async def test_get_refinement_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id = await _setup_transcription(client, "test-get-404")
        resp = await client.get(f"/api/refine/{txn_id}")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_refinement():
    mock_provider = AsyncMock()
    mock_provider.generate_refinement.return_value = LLMRefinementResponse(
        utterances=[Utterance(start=0, end=5000, text="Hello.", speaker="Speaker 1"),
                    Utterance(start=5000, end=10000, text="Hi.", speaker="Speaker 2")],
        changes_summary="Fixed punctuation",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        txn_id = await _setup_transcription(client, "test-del-refine")
        with patch("app.routers.refinement.get_llm_provider", return_value=mock_provider):
            await client.post(f"/api/refine/{txn_id}")
        resp_del = await client.delete(f"/api/refine/{txn_id}")
        resp_get = await client.get(f"/api/refine/{txn_id}")

    assert resp_del.status_code == 200
    assert resp_get.status_code == 404
