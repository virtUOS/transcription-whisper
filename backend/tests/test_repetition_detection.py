"""A looping completion must be cut off by the server, not by our timeout.

Ornith-1.5-35B-A3B in vLLM JSON mode falls into an endless whitespace loop on
roughly a quarter of analysis requests (measured 2026-09-22: 1/1, 1/4, 2/5 on
the same 34-minute transcript). Whitespace is always valid inside the JSON
grammar, so nothing stops it: one such request generated for 27 minutes until
it hit the 262144-token context window, long after the app had given up at
600s. vLLM's per-request repetition_detection ends generation after a short
repeated pattern instead; a caught loop then comes back as truncated JSON
within seconds and the caller retries.

The server-side alternative (disable_any_whitespace) is a deploy-wide vLLM
flag, and the per-request spelling of it is ignored by vLLM v0.28 (verified
directly against the container); repetition_detection is honoured per request
and forwarded by litellm.
"""
import asyncio

import pytest

from app.config import settings


def test_repetition_detection_is_on_by_default():
    assert settings.LLM_STOP_ON_REPETITION is True


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "virtUOS")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/v1")
    import importlib
    from app import config
    importlib.reload(config)
    from app.services.llm import openai as openai_module
    importlib.reload(openai_module)
    return openai_module.OpenAIProvider()


def _response(content, finish_reason="stop"):
    class _M:
        pass
    m = _M(); m.content = content
    class _C:
        pass
    c = _C(); c.message = m; c.finish_reason = finish_reason
    class _R:
        pass
    r = _R(); r.choices = [c]; r.usage = None
    return r


def test_json_chat_sends_repetition_detection(provider, monkeypatch):
    seen = {}

    async def fake_create(**kwargs):
        seen.update(kwargs)
        return _response("{}")

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    asyncio.run(provider._json_chat("sys", "user", "analysis"))

    rd = (seen.get("extra_body") or {}).get("repetition_detection")
    assert rd, f"expected repetition_detection in extra_body, got {seen.get('extra_body')!r}"
    assert rd["max_pattern_size"] >= 1
    assert rd["min_count"] >= 2, "vLLM rejects min_count < 2"
    assert rd["min_pattern_size"] <= rd["max_pattern_size"]


@pytest.mark.parametrize("operation", ["translation", "refinement"])
def test_utterance_echo_paths_do_not_send_repetition_detection(provider, monkeypatch, operation):
    """Translation and refinement echo every utterance back, so a transcript
    with a hallucination loop ("Thank you." sixty times) makes a legitimate
    reply repeat a short pattern well past min_count. On 2026-10-07 the
    detector cut such a translation mid-string on every retry and the whole
    translation failed; refinement keeps the original text in that case, so it
    lost the chunk silently. Their output is already bounded by
    REFINEMENT_OUTPUT_TOKEN_CAP, so a runaway there cannot reach the context
    window anyway."""
    seen = {}

    async def fake_create(**kwargs):
        seen.update(kwargs)
        return _response("{}")

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    asyncio.run(provider._json_chat("sys", "user", operation, max_tokens=100))
    assert "repetition_detection" not in (seen.get("extra_body") or {})


def test_repetition_detection_is_omitted_when_disabled(provider, monkeypatch):
    from app.services.llm import openai as openai_module
    monkeypatch.setattr(openai_module.settings, "LLM_STOP_ON_REPETITION", False)
    seen = {}

    async def fake_create(**kwargs):
        seen.update(kwargs)
        return _response("{}")

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    asyncio.run(provider._json_chat("sys", "user", "analysis"))
    assert "repetition_detection" not in (seen.get("extra_body") or {})


def test_json_chat_rejects_a_truncated_completion(provider, monkeypatch):
    """finish_reason=length means the cap cut the reply: the JSON is incomplete
    even if it happens to parse (a string closed by the cap), so fail loudly."""
    async def fake_create(**kwargs):
        return _response('{"summary": "abc', finish_reason="length")

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    with pytest.raises(ValueError, match="truncated|length"):
        asyncio.run(provider._json_chat("sys", "user", "analysis", max_tokens=100))
