"""Reasoning tokens must not be spent on the utterance-rewriting paths.

Ornith-1.5-35B-A3B is a reasoning model: it emits reasoning_content before any
answer. Measured against the deployed endpoint on one real 50-utterance
refinement chunk:

    with reasoning     FAILED after 900s (timeout)
    without reasoning  113s, returned 50/50

On a trivial prompt ("Reply with the single word: ok") it spent 30 reasoning
tokens to produce 4 characters. Refinement makes the model reason over all 50
utterances before emitting a single character of JSON, which is what pushed
chunks past even a 600s ceiling — ten separate chunks timed out during one
1489-utterance run.

Nondeterministic reasoning length also explains the latency variance that looked
inexplicable: the same chunk took 108s and 237s on identical input.
"""
import pytest

from app.config import settings


def test_thinking_is_disabled_by_default():
    assert settings.LLM_DISABLE_THINKING is True, (
        "reasoning tokens make refinement chunks exceed even a 600s timeout"
    )


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


def test_json_chat_sends_the_disable_thinking_flag(provider, monkeypatch):
    """vLLM takes this through chat_template_kwargs in the request body."""
    seen = {}

    async def fake_create(**kwargs):
        seen.update(kwargs)
        class _M:
            content = '{"utterances": [], "changes_summary": "x"}'
        class _C:
            message = _M()
        class _R:
            choices = [_C()]
            usage = None
        return _R()

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    import asyncio
    asyncio.run(provider._json_chat("sys", "user", "refinement"))

    extra = seen.get("extra_body") or {}
    assert extra.get("chat_template_kwargs", {}).get("enable_thinking") is False, (
        f"expected enable_thinking=False in extra_body, got {seen.get('extra_body')!r}"
    )


def test_flag_is_omitted_when_disabled(provider, monkeypatch):
    """A model that does not understand the flag must not receive it."""
    # The provider module was reloaded by the fixture, so patch the settings
    # object it actually closed over rather than the one imported at top level.
    from app.services.llm import openai as openai_module
    monkeypatch.setattr(openai_module.settings, "LLM_DISABLE_THINKING", False)
    seen = {}

    async def fake_create(**kwargs):
        seen.update(kwargs)
        class _M:
            content = "{}"
        class _C:
            message = _M()
        class _R:
            choices = [_C()]
            usage = None
        return _R()

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)
    import asyncio
    asyncio.run(provider._json_chat("sys", "user", "refinement"))
    assert not seen.get("extra_body"), "flag must be omitted when not enabled"
