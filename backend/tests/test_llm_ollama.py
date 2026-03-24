import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_generate_summary():
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": json.dumps({
                "summary": "Test summary",
                "chapters": [
                    {"title": "Intro", "start_time": 0, "end_time": 60000, "summary": "Introduction"}
                ],
            })
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.llm.ollama.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await provider.generate_summary("[00:00:00] Hello world")

    assert result.summary == "Test summary"
    assert len(result.chapters) == 1


@pytest.mark.asyncio
async def test_generate_protocol():
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": json.dumps({
                "title": "Team Meeting",
                "participants": ["Alice"],
                "key_points": [
                    {"topic": "Budget", "speaker": "Alice", "timestamp": 1000, "content": "Approved"}
                ],
                "decisions": [],
                "action_items": [],
            })
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.llm.ollama.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await provider.generate_protocol("[00:00:00] Alice: Budget approved")

    assert result.title == "Team Meeting"
    assert len(result.key_points) == 1


@pytest.mark.asyncio
async def test_generate_refinement():
    provider = OllamaProvider()

    utterances = [
        {"start": 0, "end": 3000, "text": "Helo world", "speaker": "Speaker 1"},
        {"start": 3000, "end": 6000, "text": "This is a test", "speaker": "Speaker 2"},
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": json.dumps({
                "utterances": [
                    {"start": 0, "end": 3000, "text": "Hello world", "speaker": "Speaker 1"},
                    {"start": 3000, "end": 6000, "text": "This is a test", "speaker": "Speaker 2"},
                ],
                "changes_summary": "Fixed typo in first utterance",
            })
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.llm.ollama.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await provider.generate_refinement(json.dumps(utterances))

    assert len(result.utterances) == 2
    assert result.utterances[0].text == "Hello world"
    assert result.changes_summary == "Fixed typo in first utterance"
