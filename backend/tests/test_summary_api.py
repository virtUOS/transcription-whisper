import json
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models import SummaryResult, SummaryChapter


@pytest.mark.asyncio
async def test_summarize_endpoint():
    mock_provider = AsyncMock()
    mock_provider.generate_summary.return_value = SummaryResult(
        summary="Test summary",
        chapters=[SummaryChapter(title="Intro", start_time=0, end_time=60000, summary="Introduction")],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup: upload + fake transcription in DB
        upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
        file_id = upload_resp.json()["id"]

        # Insert a completed transcription directly into DB
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("test-txn", "anonymous", file_id, "murmurai", "completed",
                 json.dumps([{"start": 0, "end": 5000, "text": "Hello world", "speaker": "Speaker 1"}])),
            )
            await db.commit()

        with patch("app.routers.summary.get_llm_provider", return_value=mock_provider):
            resp = await client.post("/api/summarize/test-txn")

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"] == "Test summary"
    assert len(data["chapters"]) == 1


@pytest.mark.asyncio
async def test_summarize_with_chapter_hints():
    mock_provider = AsyncMock()
    mock_provider.generate_summary.return_value = SummaryResult(
        summary="Guided summary",
        chapters=[
            SummaryChapter(title="Intro", start_time=0, end_time=30000, summary="Introduction section"),
            SummaryChapter(title="Methods", start_time=30000, end_time=60000, summary="Methods section"),
        ],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
        file_id = upload_resp.json()["id"]

        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("test-hints", "anonymous", file_id, "murmurai", "completed",
                 json.dumps([{"start": 0, "end": 5000, "text": "Hello world", "speaker": "Speaker 1"}])),
            )
            await db.commit()

        with patch("app.routers.summary.get_llm_provider", return_value=mock_provider):
            resp = await client.post(
                "/api/summarize/test-hints",
                json={"chapter_hints": [
                    {"title": "Intro", "description": "Introduction"},
                    {"title": "Methods"},
                ]},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"] == "Guided summary"
    assert len(data["chapters"]) == 2
    assert data["chapter_hints"] is not None
    assert len(data["chapter_hints"]) == 2
    # Verify hints were passed to provider
    mock_provider.generate_summary.assert_called_once()
    args, kwargs = mock_provider.generate_summary.call_args
    assert len(args) >= 2 and args[1] is not None
    assert args[1][0].title == "Intro"


@pytest.mark.asyncio
async def test_summarize_rejects_empty_hints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/summarize/any-id",
            json={"chapter_hints": [{"title": None, "description": None}]},
        )
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_summarize_cache_returns_on_no_body():
    """A POST with no body should return the cached summary even if it was generated with hints."""
    mock_provider = AsyncMock()
    mock_provider.generate_summary.return_value = SummaryResult(
        summary="Cached",
        chapters=[SummaryChapter(title="Ch1", start_time=0, end_time=10000, summary="Chapter 1")],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
        file_id = upload_resp.json()["id"]

        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("test-cache", "anonymous", file_id, "murmurai", "completed",
                 json.dumps([{"start": 0, "end": 5000, "text": "Hello", "speaker": "Speaker 1"}])),
            )
            await db.commit()

        with patch("app.routers.summary.get_llm_provider", return_value=mock_provider):
            # First call with hints — generates
            resp1 = await client.post("/api/summarize/test-cache", json={"chapter_hints": [{"title": "Ch1", "description": "test"}]})
            assert resp1.status_code == 200
            # Second call with no body — should return cache, not regenerate
            resp2 = await client.post("/api/summarize/test-cache")
            assert resp2.status_code == 200
            assert resp2.json()["summary"] == "Cached"
            # Provider should only be called once (first request)
            assert mock_provider.generate_summary.call_count == 1


@pytest.mark.asyncio
async def test_summarize_cache_invalidation_on_different_hints():
    """A POST with different hints should regenerate the summary."""
    call_count = 0

    async def mock_generate(transcript, chapter_hints=None):
        nonlocal call_count
        call_count += 1
        return SummaryResult(
            summary=f"Summary {call_count}",
            chapters=[SummaryChapter(title="Ch", start_time=0, end_time=10000, summary="chapter")],
        )

    mock_provider = AsyncMock()
    mock_provider.generate_summary = mock_generate

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post("/api/upload", files={"file": ("test.mp3", b"fake", "audio/mpeg")})
        file_id = upload_resp.json()["id"]

        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                """INSERT INTO transcriptions (id, user_id, file_id, asr_backend, status, result_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("test-inval", "anonymous", file_id, "murmurai", "completed",
                 json.dumps([{"start": 0, "end": 5000, "text": "Hello", "speaker": "Speaker 1"}])),
            )
            await db.commit()

        with patch("app.routers.summary.get_llm_provider", return_value=mock_provider):
            resp1 = await client.post("/api/summarize/test-inval", json={"chapter_hints": [{"title": "Intro"}]})
            assert resp1.status_code == 200
            assert resp1.json()["summary"] == "Summary 1"

            resp2 = await client.post("/api/summarize/test-inval", json={"chapter_hints": [{"title": "Different"}]})
            assert resp2.status_code == 200
            assert resp2.json()["summary"] == "Summary 2"
            assert call_count == 2
