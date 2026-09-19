"""The token counter must carry the same provider label as the request,
error and duration metrics, which all use settings.LLM_PROVIDER. The SDK
name ("openai", "ollama") is not the provider: the production deployment
talks to virtUOS through the OpenAI SDK.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm.ollama import OllamaProvider
from app.services.llm.openai import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_labels_tokens_with_configured_provider(monkeypatch):
    monkeypatch.setattr("app.services.llm.openai.settings.LLM_PROVIDER", "virtUOS")
    provider = OpenAIProvider()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "A title"
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=3)

    with patch.object(provider, "_client") as mock_client, \
         patch("app.services.llm.openai.track_llm_tokens") as track:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        await provider.generate_title("Hello world")

    track.assert_called_once()
    assert track.call_args.args[0] == "virtUOS"


@pytest.mark.asyncio
async def test_ollama_provider_labels_tokens_with_configured_provider(monkeypatch):
    monkeypatch.setattr("app.services.llm.ollama.settings.LLM_PROVIDER", "my-ollama")
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"content": json.dumps({"summary": "s", "chapters": []})},
        "prompt_eval_count": 10,
        "eval_count": 3,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.llm.ollama.httpx.AsyncClient") as MockClient, \
         patch("app.services.llm.ollama.track_llm_tokens") as track:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client
        await provider.generate_summary("[00:00:00] Hello world")

    track.assert_called_once()
    assert track.call_args.args[0] == "my-ollama"
