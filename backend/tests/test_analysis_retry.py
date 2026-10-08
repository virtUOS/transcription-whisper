"""Analysis LLM calls carry an output cap and retry once on a bad reply.

Analysis had no max_tokens at all, so a looping completion ran for 27 minutes
against a 600s app timeout (see test_repetition_detection). Even with the
server cutting loops short, the caught loop arrives as truncated JSON, and the
loop is nondeterministic (about 1 in 4), so one retry turns most failures into
a result a few seconds later.

A reply that reached the output cap is the exception: the same request needs
the same output, so it is not retried (2026-10-08: 4 of 4 attempts hit it).
"""
import json

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.config import settings
from app.services.llm.base import analysis_json_chat, ANALYSIS_RETRIES, LLMProvider, OutputLimitExceeded
from app.services.llm.openai import OpenAIProvider
from app.services.llm.prompt import ANALYSIS_OUTPUT_TOKEN_CAP


def test_cap_clears_a_real_summary_by_a_wide_margin():
    """Real summaries of a 34-minute transcript measured 1350-2150 completion
    tokens; protocols and multi-chunk consolidations run longer."""
    assert ANALYSIS_OUTPUT_TOKEN_CAP >= 2150 * 3


def test_cap_clears_a_long_custom_prompt_analysis():
    """A custom prompt sets the output size, not the template. On 2026-10-08 a
    custom-prompt analysis of an 85-minute transcript reached 8192 output
    tokens on 4 of 4 attempts, with the repetition detector on."""
    assert ANALYSIS_OUTPUT_TOKEN_CAP > 8192


def test_a_capped_reply_still_arrives_before_the_request_timeout():
    """Output past LLM_TIMEOUT is generated for nobody: the app has given up,
    and litellm does not pass the disconnect on to vLLM. 79 tok/s is the
    slowest throughput measured on the shared endpoint (2026-09-18)."""
    assert ANALYSIS_OUTPUT_TOKEN_CAP / 79 < settings.LLM_TIMEOUT


@pytest.mark.asyncio
async def test_passes_the_cap_to_json_chat():
    provider = MagicMock(spec=LLMProvider)
    provider._json_chat = AsyncMock(return_value={"ok": True})
    assert await analysis_json_chat(provider, "sys", "user") == {"ok": True}
    provider._json_chat.assert_awaited_once_with("sys", "user", "analysis", max_tokens=ANALYSIS_OUTPUT_TOKEN_CAP)


@pytest.mark.asyncio
async def test_retries_once_after_malformed_json():
    provider = MagicMock(spec=LLMProvider)
    provider._json_chat = AsyncMock(side_effect=[json.JSONDecodeError("x", "{", 1), {"summary": "ok"}])
    assert await analysis_json_chat(provider, "sys", "user") == {"summary": "ok"}
    assert provider._json_chat.await_count == 2


@pytest.mark.asyncio
async def test_retries_once_after_a_rejected_reply():
    provider = MagicMock(spec=LLMProvider)
    provider._json_chat = AsyncMock(side_effect=[ValueError("schema echoed back"), {"summary": "ok"}])
    assert await analysis_json_chat(provider, "sys", "user") == {"summary": "ok"}
    assert provider._json_chat.await_count == 2


@pytest.mark.asyncio
async def test_a_reply_that_reached_the_output_cap_is_not_retried():
    """The repetition detector stops the known loop long before the cap, so a
    reply that reaches it was asked for that much output; a retry hits the cap
    again and doubles a wait of several minutes."""
    provider = MagicMock(spec=LLMProvider)
    provider._json_chat = AsyncMock(side_effect=[OutputLimitExceeded("cap"), {"summary": "ok"}])
    with pytest.raises(OutputLimitExceeded):
        await analysis_json_chat(provider, "sys", "user")
    assert provider._json_chat.await_count == 1


@pytest.mark.asyncio
async def test_gives_up_after_the_retries_with_a_user_facing_error():
    provider = MagicMock(spec=LLMProvider)
    provider._json_chat = AsyncMock(side_effect=json.JSONDecodeError("x", "{", 1))
    with pytest.raises(ValueError, match="malformed"):
        await analysis_json_chat(provider, "sys", "user")
    assert provider._json_chat.await_count == ANALYSIS_RETRIES + 1


@pytest.mark.asyncio
async def test_a_transport_error_is_not_retried_here():
    """Timeouts and connection errors are a different failure; the caller and
    its metrics handle them, and a blind re-send would double the wait."""
    provider = MagicMock(spec=LLMProvider)
    provider._json_chat = AsyncMock(side_effect=RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        await analysis_json_chat(provider, "sys", "user")
    assert provider._json_chat.await_count == 1


@pytest.mark.asyncio
async def test_generate_summary_recovers_from_one_bad_reply():
    provider = OpenAIProvider()
    good = {"summary": "Fine.", "chapters": [], "language": "en"}
    provider._json_chat = AsyncMock(side_effect=[json.JSONDecodeError("x", "{", 1), good])
    result = await provider.generate_summary("[00:00:00] Hello world")
    assert result.summary == "Fine."
    assert provider._json_chat.await_count == 2
    assert provider._json_chat.await_args.kwargs["max_tokens"] == ANALYSIS_OUTPUT_TOKEN_CAP
