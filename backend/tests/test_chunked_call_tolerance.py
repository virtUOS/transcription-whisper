"""Opt-in tolerance for a chunk that exhausts its retries.

Default behaviour (raise, cancel siblings) is what translation needs and is
covered by test_chunk_timeout_resilience.py. Refinement opts in, because an
unrefined range is still correct text while an untranslated one is not.
"""
import asyncio
import json

import pytest

from app.services.llm.base import LLMProvider, chunked_utterance_call


def _utterances(n):
    return [
        {"start": i * 1000, "end": i * 1000 + 500, "speaker": "S", "text": f"line {i}"}
        for i in range(n)
    ]


class _FailsChunk(LLMProvider):
    """Fails every request for the chunk whose first utterance starts at `bad_start`."""

    def __init__(self, bad_start, mode="raise"):
        self.bad_start = bad_start
        self.mode = mode
        self.calls = []

    async def _json_chat(self, system, user, operation, max_tokens=None):
        chunk = json.loads(user)
        self.calls.append(chunk[0]["start"])
        if chunk[0]["start"] == self.bad_start:
            if self.mode == "raise":
                raise TimeoutError("simulated timeout")
            # persistent wrong count: drop one utterance every time
            return {"utterances": chunk[:-1], "changes_summary": "short"}
        return {"utterances": chunk, "changes_summary": f"ok {chunk[0]['start']}"}

    async def _consolidate_refinement_summaries(self, summaries):
        return " | ".join(summaries)

    async def generate_title(self, transcript):
        return "title"


@pytest.mark.asyncio
async def test_default_still_raises():
    provider = _FailsChunk(bad_start=50_000)
    with pytest.raises(TimeoutError):
        await chunked_utterance_call(
            provider, _utterances(150), build_system=lambda: "sys",
            operation="refinement", expect_same_count=True,
        )


@pytest.mark.asyncio
async def test_tolerated_request_failure_yields_none_in_place():
    provider = _FailsChunk(bad_start=50_000)
    results = await chunked_utterance_call(
        provider, _utterances(150), build_system=lambda: "sys",
        operation="refinement", expect_same_count=True, tolerate_failures=True,
    )
    assert len(results) == 3
    assert results[1] is None
    assert results[0]["utterances"][0]["start"] == 0
    assert results[2]["utterances"][0]["start"] == 100_000


@pytest.mark.asyncio
async def test_tolerated_wrong_count_yields_none_in_place():
    provider = _FailsChunk(bad_start=0, mode="short")
    results = await chunked_utterance_call(
        provider, _utterances(100), build_system=lambda: "sys",
        operation="refinement", expect_same_count=True, tolerate_failures=True,
    )
    assert results[0] is None
    assert results[1] is not None


@pytest.mark.asyncio
async def test_siblings_are_not_cancelled_when_one_chunk_is_tolerated():
    provider = _FailsChunk(bad_start=50_000)
    await chunked_utterance_call(
        provider, _utterances(150), build_system=lambda: "sys",
        operation="refinement", expect_same_count=True, tolerate_failures=True,
    )
    # the healthy chunks were each sent exactly once and finished
    assert provider.calls.count(0) == 1
    assert provider.calls.count(100_000) == 1


@pytest.mark.asyncio
async def test_cancellation_still_propagates_when_tolerating():
    class _Hangs(LLMProvider):
        async def _json_chat(self, system, user, operation, max_tokens=None):
            await asyncio.sleep(10)
            return {}

        async def _consolidate_refinement_summaries(self, summaries):
            return ""

        async def generate_title(self, transcript):
            return ""

    task = asyncio.ensure_future(chunked_utterance_call(
        _Hangs(), _utterances(10), build_system=lambda: "sys",
        operation="refinement", tolerate_failures=True,
    ))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_explicit_chunks_bypass_chunking():
    provider = _FailsChunk(bad_start=-1)  # never fails
    utts = _utterances(200)
    results = await chunked_utterance_call(
        provider, utts, build_system=lambda: "sys",
        operation="refinement", expect_same_count=True,
        chunks=[utts[50:100], utts[150:200]],
    )
    assert len(results) == 2
    assert provider.calls == [50_000, 150_000]
