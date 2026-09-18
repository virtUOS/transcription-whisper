"""Chunk boundaries must be reproducible from the utterance count alone.

Refinement stores the ranges that failed and later retries exactly those, so
the ranges and the chunks actually sent have to come from one function.
"""
from app.services.llm.prompt import chunk_ranges, chunk_utterances_for_refinement


def test_short_transcript_is_one_range():
    assert chunk_ranges(10) == [(0, 10)]


def test_exact_multiple_has_no_empty_tail():
    assert chunk_ranges(100) == [(0, 50), (50, 100)]


def test_last_range_is_short():
    # 841 utterances is the production transcript that motivated this work.
    ranges = chunk_ranges(841)
    assert len(ranges) == 17
    assert ranges[0] == (0, 50)
    assert ranges[-1] == (800, 841)


def test_ranges_are_contiguous_and_cover_everything():
    ranges = chunk_ranges(850)
    assert ranges[0][0] == 0
    assert ranges[-1][1] == 850
    for (_, prev_end), (next_start, _) in zip(ranges, ranges[1:]):
        assert prev_end == next_start


def test_empty_transcript_has_no_ranges():
    assert chunk_ranges(0) == []


def test_chunker_slices_exactly_along_chunk_ranges():
    utterances = [{"start": i, "end": i + 1, "text": f"u{i}"} for i in range(841)]
    chunks = chunk_utterances_for_refinement(utterances)
    assert [(c[0]["start"], c[-1]["start"] + 1) for c in chunks] == chunk_ranges(841)


def test_chunker_honours_custom_size_through_chunk_ranges():
    utterances = [{"start": i, "end": i + 1, "text": f"u{i}"} for i in range(10)]
    chunks = chunk_utterances_for_refinement(utterances, max_utterances=3)
    assert [len(c) for c in chunks] == [3, 3, 3, 1]
    assert chunk_ranges(10, max_utterances=3) == [(0, 3), (3, 6), (6, 9), (9, 10)]
