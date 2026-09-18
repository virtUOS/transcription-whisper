import asyncio
import json

import pytest

from app.services.llm.base import LLMProvider
from app.services.llm.prompt import chunk_utterances_for_refinement


def _utterances(n, start=0):
    return [
        {"start": (start + i) * 1000, "end": (start + i) * 1000 + 500,
         "speaker": "SPEAKER_00", "text": f"line {start + i}"}
        for i in range(n)
    ]


class _FakeProvider(LLMProvider):
    """Returns each chunk unchanged, slowest chunk first, to prove that
    results are reassembled in input order rather than completion order."""

    def __init__(self):
        self.calls = 0
        self.concurrent = 0
        self.max_concurrent = 0

    async def _json_chat(self, system, user, operation, max_tokens=None):
        self.calls += 1
        self.concurrent += 1
        self.max_concurrent = max(self.max_concurrent, self.concurrent)
        chunk = json.loads(user)
        # Earlier chunks sleep longer, so completion order is the reverse of
        # input order. A correct implementation still returns them in order.
        await asyncio.sleep(0.05 / (chunk[0]["start"] / 1000 + 1))
        self.concurrent -= 1
        return {"utterances": chunk, "changes_summary": f"chunk at {chunk[0]['start']}"}

    async def _consolidate_refinement_summaries(self, summaries):
        return " | ".join(summaries)

    async def generate_title(self, transcript):
        return "title"


@pytest.mark.asyncio
async def test_refinement_preserves_utterance_order_across_chunks():
    utterances = _utterances(150)
    provider = _FakeProvider()
    result = await provider.generate_refinement(json.dumps(utterances))

    assert len(result.utterances) == len(utterances)
    starts = [u.start for u in result.utterances]
    assert starts == sorted(starts), "utterances came back out of order"
    assert [u.text for u in result.utterances] == [u["text"] for u in utterances]


@pytest.mark.asyncio
async def test_refinement_runs_chunks_concurrently():
    utterances = _utterances(150)
    provider = _FakeProvider()
    await provider.generate_refinement(json.dumps(utterances))

    assert provider.calls > 1, "expected the transcript to be chunked"
    assert provider.max_concurrent > 1, (
        "chunks were sent sequentially; a long refinement then takes the sum of "
        "every chunk's latency, which is minutes"
    )


def test_chunk_size_fits_inside_a_single_request():
    """A chunk must be small enough to generate within LLM_TIMEOUT. Measured at
    roughly 178 tok/s and ~280 output tokens per utterance, 50 utterances is
    about 79s; 200 would need over 300s and always timed out."""
    chunks = chunk_utterances_for_refinement(_utterances(248))
    assert all(len(c) <= 50 for c in chunks)
    assert sum(len(c) for c in chunks) == 248
