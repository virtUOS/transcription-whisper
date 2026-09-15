import asyncio
import json

import pytest

from app.services.llm.base import LLMProvider, chunked_utterance_call


def _utterances(n):
    return [
        {"start": i * 1000, "end": i * 1000 + 500,
         "speaker": "SPEAKER_00", "text": f"line {i}"}
        for i in range(n)
    ]


class _DropsOnce(LLMProvider):
    """Returns one utterance too few on the first attempt at a given chunk.

    Models do not reliably honour "return exactly the same number of
    utterances": observed in production returning 247 of 248, which discarded
    all five chunks' work and surfaced as a 500 after several minutes.
    """

    def __init__(self, drop_for_start=0):
        self.drop_for_start = drop_for_start
        self.attempts = 0
        self.dropped_once = False

    async def _json_chat(self, system, user, operation):
        self.attempts += 1
        chunk = json.loads(user)
        await asyncio.sleep(0)
        if chunk[0]["start"] == self.drop_for_start and not self.dropped_once:
            self.dropped_once = True
            return {"utterances": chunk[:-1], "changes_summary": "dropped one"}
        return {"utterances": chunk, "changes_summary": "ok"}

    async def _consolidate_refinement_summaries(self, summaries):
        return " | ".join(summaries)

    async def generate_title(self, transcript):
        return "t"


class _AlwaysDrops(_DropsOnce):
    async def _json_chat(self, system, user, operation):
        self.attempts += 1
        chunk = json.loads(user)
        await asyncio.sleep(0)
        return {"utterances": chunk[:-1], "changes_summary": "dropped one"}


@pytest.mark.asyncio
async def test_a_chunk_returning_the_wrong_count_is_retried():
    provider = _DropsOnce(drop_for_start=0)
    utterances = _utterances(150)
    results = await chunked_utterance_call(
        provider, utterances,
        build_system=lambda: "sys",
        operation="refinement",
        expect_same_count=True,
    )
    merged = [u for data in results for u in data.get("utterances", [])]
    assert len(merged) == 150, "the short chunk should have been retried"
    assert provider.attempts == 4, "3 chunks + 1 retry, not a full redo"


@pytest.mark.asyncio
async def test_only_the_failing_chunk_is_retried_not_the_whole_job():
    provider = _DropsOnce(drop_for_start=100 * 1000)
    await chunked_utterance_call(
        provider, _utterances(150),
        build_system=lambda: "sys",
        operation="refinement",
        expect_same_count=True,
    )
    assert provider.attempts == 4


@pytest.mark.asyncio
async def test_a_chunk_that_never_matches_still_raises():
    provider = _AlwaysDrops()
    with pytest.raises(ValueError, match="utterance"):
        await chunked_utterance_call(
            provider, _utterances(150),
            build_system=lambda: "sys",
            operation="refinement",
            expect_same_count=True,
        )


@pytest.mark.asyncio
async def test_count_is_not_enforced_when_not_requested():
    """Analysis-style calls do not return one item per input utterance."""
    provider = _AlwaysDrops()
    results = await chunked_utterance_call(
        provider, _utterances(60),
        build_system=lambda: "sys",
        operation="analysis",
    )
    assert results, "should not raise when expect_same_count is off"
