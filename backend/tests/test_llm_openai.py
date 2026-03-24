import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm.openai import OpenAIProvider


@pytest.mark.asyncio
async def test_generate_summary_parses_response():
    provider = OpenAIProvider()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "summary": "Test summary",
        "chapters": [
            {"title": "Intro", "start_time": 0, "end_time": 60000, "summary": "Introduction"}
        ],
    })

    with patch.object(provider, "_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await provider.generate_summary("[00:00:00] Hello world")

    assert result.summary == "Test summary"
    assert len(result.chapters) == 1
    assert result.chapters[0].title == "Intro"


@pytest.mark.asyncio
async def test_generate_protocol_parses_response():
    provider = OpenAIProvider()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "title": "Weekly Standup",
        "participants": ["Alice", "Bob"],
        "key_points": [
            {"topic": "Sprint progress", "speaker": "Alice", "timestamp": 5000, "content": "On track"}
        ],
        "decisions": [
            {"decision": "Ship on Friday", "timestamp": 30000}
        ],
        "action_items": [
            {"task": "Update docs", "assignee": "Bob", "timestamp": 45000}
        ],
    })

    with patch.object(provider, "_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await provider.generate_protocol("[00:00:00] Alice: Hello")

    assert result.title == "Weekly Standup"
    assert len(result.participants) == 2
    assert len(result.key_points) == 1
    assert result.key_points[0].speaker == "Alice"
    assert len(result.decisions) == 1
    assert len(result.action_items) == 1
