import pytest
from app.services.source_tracking import hash_utterance_texts, select_source


def test_hash_is_stable_across_invocations():
    utt = [{"start": 0, "end": 1, "text": "hello", "speaker": "A"}]
    assert hash_utterance_texts(utt) == hash_utterance_texts(utt)


def test_hash_ignores_timestamp_and_speaker_changes():
    a = [{"start": 0, "end": 1000, "text": "hello", "speaker": "A"}]
    b = [{"start": 500, "end": 2000, "text": "hello", "speaker": "B"}]
    assert hash_utterance_texts(a) == hash_utterance_texts(b)


def test_hash_changes_when_text_changes():
    a = [{"start": 0, "end": 1, "text": "hello", "speaker": "A"}]
    b = [{"start": 0, "end": 1, "text": "hello!", "speaker": "A"}]
    assert hash_utterance_texts(a) != hash_utterance_texts(b)


def test_hash_respects_utterance_order():
    a = [{"text": "one"}, {"text": "two"}]
    b = [{"text": "two"}, {"text": "one"}]
    assert hash_utterance_texts(a) != hash_utterance_texts(b)


def test_hash_empty_list_is_stable():
    assert hash_utterance_texts([]) == hash_utterance_texts([])


def test_hash_is_hex_sha256():
    h = hash_utterance_texts([{"text": "x"}])
    assert len(h) == 64
    int(h, 16)  # raises if not hex


def test_select_source_explicit_refined_requires_refined():
    with pytest.raises(ValueError):
        select_source(explicit="refined", result_json="[]", refined_json=None)


def test_select_source_explicit_original_ok():
    assert select_source(explicit="original", result_json="[]", refined_json=None) == "original"
    assert select_source(explicit="original", result_json="[]", refined_json="[]") == "original"


def test_select_source_default_prefers_refined_when_available():
    assert select_source(explicit=None, result_json="[]", refined_json="[{}]") == "refined"


def test_select_source_default_falls_back_to_original():
    assert select_source(explicit=None, result_json="[]", refined_json=None) == "original"


def test_select_source_treats_empty_refined_sentinel_as_unavailable():
    # The in-progress sentinel is ''; it should not count as a valid refined source.
    assert select_source(explicit=None, result_json="[]", refined_json="") == "original"
