from app.models import Utterance
from app.services.formats import generate_srt, generate_vtt, generate_txt


UTTERANCES = [
    Utterance(start=1000, end=5000, text="Hello world", speaker="Speaker 1"),
    Utterance(start=5000, end=10000, text="How are you", speaker="Speaker 2"),
]

SPEAKER_MAP = {"Speaker 1": "Alice", "Speaker 2": "Bob"}


def test_generate_srt_with_speakers():
    result = generate_srt(UTTERANCES)
    assert "1\n00:00:01,000 --> 00:00:05,000\n[Speaker 1]: Hello world" in result
    assert "2\n00:00:05,000 --> 00:00:10,000\n[Speaker 2]: How are you" in result


def test_generate_srt_with_speaker_mappings():
    result = generate_srt(UTTERANCES, SPEAKER_MAP)
    assert "[Alice]: Hello world" in result
    assert "[Bob]: How are you" in result


def test_generate_vtt():
    result = generate_vtt(UTTERANCES)
    assert result.startswith("WEBVTT")
    assert "00:00:01.000 --> 00:00:05.000" in result


def test_generate_txt():
    result = generate_txt(UTTERANCES)
    assert "[Speaker 1]: Hello world" in result


def test_generate_txt_without_speakers():
    utterances = [Utterance(start=0, end=1000, text="Just text")]
    result = generate_txt(utterances)
    assert result == "Just text"
