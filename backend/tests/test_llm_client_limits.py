import pytest

from app.config import settings
from app.services.llm.base import LLM_CHUNK_MAX_CONCURRENT


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


def test_timeout_is_applied(provider):
    assert provider._client.timeout == settings.LLM_TIMEOUT


def test_retries_are_configured_explicitly(provider):
    """Pinned rather than left to the SDK default, so the value is a decision
    someone made.

    That decision is now zero. Retrying a failed chunk moved up into
    chunked_utterance_call, which re-validates the returned utterance count; the
    SDK's blind re-send does not, and layering the two multiplies worst-case
    wall clock instead of adding to it. See test_retry_amplification.py.
    """
    assert provider._client.max_retries == settings.LLM_MAX_RETRIES
    assert settings.LLM_MAX_RETRIES == 0


def test_peak_requests_per_operation_stays_small():
    """The LLM endpoint is shared with other services. The number of requests one
    refinement or translation can have in flight at once is what degrades other
    users' latency, so it is capped well below what would minimise our own
    wall-clock time.
    """
    peak_in_flight = LLM_CHUNK_MAX_CONCURRENT
    assert peak_in_flight <= 2, (
        "raising chunk concurrency increases our peak footprint on an endpoint "
        "shared with interactive users"
    )


def test_a_long_transcript_cannot_fan_out_without_bound():
    """Chunk count grows with transcript length; concurrency must not."""
    from app.services.llm.prompt import chunk_utterances_for_refinement

    utterances = [
        {"start": i * 1000, "end": i * 1000 + 500, "text": "x", "speaker": "A"}
        for i in range(2000)
    ]
    chunks = chunk_utterances_for_refinement(utterances)
    assert len(chunks) == 40, "2000 utterances at 50 per chunk"
    # However many chunks there are, only this many are ever in flight.
    assert LLM_CHUNK_MAX_CONCURRENT <= 2
