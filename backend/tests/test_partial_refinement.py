"""generate_refinement survives a dead chunk and says which one.

Production 2026-09-18, transcription fe12e5a1 (841 utterances, 17 chunks): one
chunk timed out at 600s three times, twice in a row across two attempts; the
other sixteen were fine each time. The user got nothing. After this, they get
sixteen refined chunks and a list of what to retry.
"""
import json

import pytest

from app.models import RefinementMetadata
from app.services.llm import base as base_module
from app.services.llm.base import LLMProvider


def _utterances(n):
    return [
        {"start": i * 1000, "end": i * 1000 + 500, "speaker": "S", "text": f"line {i}"}
        for i in range(n)
    ]


class _FailsRanges(LLMProvider):
    """Upper-cases every chunk except those starting at a `bad_starts` value, which always time out."""

    def __init__(self, bad_starts=()):
        self.bad_starts = set(bad_starts)
        self.sent_starts = []
        self.consolidated = None

    async def _json_chat(self, system, user, operation, max_tokens=None):
        chunk = json.loads(user)
        self.sent_starts.append(chunk[0]["start"])
        if chunk[0]["start"] in self.bad_starts:
            raise TimeoutError("simulated")
        return {
            "utterances": [{**u, "text": u["text"].upper()} for u in chunk],
            "changes_summary": f"upper-cased from {chunk[0]['start']}",
        }

    async def _consolidate_refinement_summaries(self, summaries):
        self.consolidated = list(summaries)
        return " | ".join(summaries)

    async def generate_title(self, transcript):
        return "t"


@pytest.mark.asyncio
async def test_failed_chunk_keeps_input_text_and_is_reported():
    provider = _FailsRanges(bad_starts={50_000})
    result = await provider.generate_refinement(json.dumps(_utterances(150)))
    assert result.failed_ranges == [(50, 100)]
    assert len(result.utterances) == 150
    assert [u.text for u in result.utterances[:50]] == [f"LINE {i}" for i in range(50)]
    assert [u.text for u in result.utterances[50:100]] == [f"line {i}" for i in range(50, 100)]
    assert [u.text for u in result.utterances[100:]] == [f"LINE {i}" for i in range(100, 150)]


@pytest.mark.asyncio
async def test_summary_excludes_failed_chunk():
    provider = _FailsRanges(bad_starts={50_000})
    result = await provider.generate_refinement(json.dumps(_utterances(150)))
    assert provider.consolidated == ["upper-cased from 0", "upper-cased from 100000"]
    assert result.changes_summary == "upper-cased from 0 | upper-cased from 100000"


@pytest.mark.asyncio
async def test_all_chunks_failing_on_an_initial_run_raises():
    provider = _FailsRanges(bad_starts={0, 50_000})
    with pytest.raises(RuntimeError):
        await provider.generate_refinement(json.dumps(_utterances(100)))


@pytest.mark.asyncio
async def test_empty_transcript_does_not_raise():
    provider = _FailsRanges()
    result = await provider.generate_refinement(json.dumps([]))
    assert result.utterances == []
    assert result.failed_ranges == []


@pytest.mark.asyncio
async def test_ranges_sends_only_those_ranges():
    provider = _FailsRanges()
    result = await provider.generate_refinement(
        json.dumps(_utterances(200)), ranges=[(50, 100), (150, 200)],
    )
    assert sorted(provider.sent_starts) == [50_000, 150_000]
    assert result.utterances[0].text == "line 0"      # outside: returned as sent
    assert result.utterances[50].text == "LINE 50"    # inside: refined
    assert result.utterances[150].text == "LINE 150"
    assert result.failed_ranges == []


@pytest.mark.asyncio
async def test_retry_where_everything_fails_again_does_not_raise():
    provider = _FailsRanges(bad_starts={50_000})
    result = await provider.generate_refinement(
        json.dumps(_utterances(100)), ranges=[(50, 100)], previous_summary="old summary",
    )
    assert result.failed_ranges == [(50, 100)]
    assert result.changes_summary == "old summary"
    assert provider.consolidated is None


@pytest.mark.asyncio
async def test_previous_summary_is_folded_into_the_new_one():
    provider = _FailsRanges()
    result = await provider.generate_refinement(
        json.dumps(_utterances(100)), ranges=[(50, 100)], previous_summary="old summary",
    )
    assert provider.consolidated == ["old summary", "upper-cased from 50000"]
    assert result.changes_summary == "old summary | upper-cased from 50000"


@pytest.mark.asyncio
async def test_failed_chunk_counter_increments_once_per_chunk(monkeypatch):
    seen = []
    monkeypatch.setattr(base_module, "inc", lambda counter, *a, amount=1: seen.append(amount))
    provider = _FailsRanges(bad_starts={0, 100_000})
    await provider.generate_refinement(json.dumps(_utterances(150)))
    assert seen == [2]


def test_metadata_defaults_failed_ranges_for_rows_written_before_this_field():
    md = RefinementMetadata(**{"changed_indices": [1], "changes_summary": "x"})
    assert md.failed_ranges == []


def test_metadata_round_trips_ranges_through_json():
    md = RefinementMetadata(changed_indices=[], changes_summary="", failed_ranges=[(450, 500)])
    raw = json.dumps(md.model_dump())
    assert json.loads(raw)["failed_ranges"] == [[450, 500]]
    assert RefinementMetadata(**json.loads(raw)).failed_ranges == [(450, 500)]
