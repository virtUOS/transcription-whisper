"""A slow chunk must not discard the whole job.

Production measurements on the deployed endpoint: one 50-utterance chunk took
108s on one call and 237s on another — byte-identical input, better than 2x
spread — against a 360s timeout. Transcripts run to 1489 utterances (30 chunks),
so at even a 5% per-chunk timeout rate a whole-job-fails design succeeds only
~21% of the time. Refinement must finish slowly rather than fail fast.
"""
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


class _TimesOutOnce(LLMProvider):
    """Raises a timeout the first time a given chunk is attempted."""

    def __init__(self, fail_for_start=0, exc=None):
        self.fail_for_start = fail_for_start
        self.exc = exc or TimeoutError("Request timed out.")
        self.attempts = 0
        self.failed_once = False

    async def _json_chat(self, system, user, operation):
        self.attempts += 1
        chunk = json.loads(user)
        await asyncio.sleep(0)
        if chunk[0]["start"] == self.fail_for_start and not self.failed_once:
            self.failed_once = True
            raise self.exc
        return {"utterances": chunk, "changes_summary": "ok"}

    async def _consolidate_refinement_summaries(self, summaries):
        return " | ".join(summaries)

    async def generate_title(self, transcript):
        return "t"


class _AlwaysTimesOut(_TimesOutOnce):
    async def _json_chat(self, system, user, operation):
        self.attempts += 1
        await asyncio.sleep(0)
        raise self.exc


@pytest.mark.asyncio
async def test_a_chunk_that_times_out_is_retried_not_fatal():
    provider = _TimesOutOnce(fail_for_start=0)
    result = await chunked_utterance_call(
        provider, _utterances(150),
        build_system=lambda: "sys",
        operation="refinement",
        expect_same_count=True,
    )
    merged = [u for data in result for u in data.get("utterances", [])]
    assert len(merged) == 150, "a single slow chunk must not discard the job"
    assert provider.attempts == 4, "3 chunks + 1 retry of the slow one"


@pytest.mark.asyncio
async def test_only_the_timing_out_chunk_is_retried():
    provider = _TimesOutOnce(fail_for_start=100 * 1000)
    await chunked_utterance_call(
        provider, _utterances(150),
        build_system=lambda: "sys",
        operation="refinement",
        expect_same_count=True,
    )
    assert provider.attempts == 4, "the other chunks' work must be kept"


@pytest.mark.asyncio
async def test_a_chunk_that_never_succeeds_still_raises():
    provider = _AlwaysTimesOut()
    with pytest.raises(Exception) as exc:
        await chunked_utterance_call(
            provider, _utterances(150),
            build_system=lambda: "sys",
            operation="refinement",
            expect_same_count=True,
        )
    assert "timed out" in str(exc.value).lower() or isinstance(exc.value, TimeoutError)


@pytest.mark.asyncio
async def test_timeout_retry_applies_without_count_checking():
    """Analysis-style calls benefit from timeout retries too."""
    provider = _TimesOutOnce(fail_for_start=0)
    result = await chunked_utterance_call(
        provider, _utterances(150),
        build_system=lambda: "sys",
        operation="analysis",
    )
    assert len(result) == 3
    assert provider.attempts == 4


@pytest.mark.asyncio
async def test_sibling_chunks_are_not_left_running_when_one_fails():
    """gather() without return_exceptions leaves siblings running as orphans.

    The failing chunk must not race ahead of still-running siblings and leave
    them writing into a job nobody is waiting for.
    """
    started = []
    finished = []

    class _SlowSibling(LLMProvider):
        async def _json_chat(self, system, user, operation):
            chunk = json.loads(user)
            started.append(chunk[0]["start"])
            if chunk[0]["start"] == 0:
                raise RuntimeError("boom")
            await asyncio.sleep(0.05)
            finished.append(chunk[0]["start"])
            return {"utterances": chunk, "changes_summary": "ok"}

        async def _consolidate_refinement_summaries(self, s):
            return ""

        async def generate_title(self, t):
            return "t"

    with pytest.raises(RuntimeError):
        await chunked_utterance_call(
            _SlowSibling(), _utterances(150),
            build_system=lambda: "sys",
            operation="refinement",
        )
    await asyncio.sleep(0.15)
    assert not finished, "siblings should be cancelled, not left running"


def test_timeout_default_clears_the_measured_worst_case():
    """The ceiling must clear a slow draw, not just the typical one.

    Measured on the deployed endpoint: the same 50-utterance chunk took 108s and
    237s. A 360s ceiling left 1.5x headroom and timed out a real refinement.
    """
    from app.config import settings
    assert settings.LLM_TIMEOUT >= 2 * 237, (
        "timeout must leave at least 2x headroom over the worst measured chunk"
    )
