import json
import pytest
from app.services.llm.prompt import (
    REFINEMENT_SCHEMA,
    build_refinement_system_prompt,
    build_refinement_user_prompt,
    chunk_utterances_for_refinement,
)


def test_refinement_schema_has_required_fields():
    assert "utterances" in REFINEMENT_SCHEMA["properties"]
    assert "changes_summary" in REFINEMENT_SCHEMA["properties"]


def test_build_refinement_system_prompt_without_context():
    prompt = build_refinement_system_prompt()
    assert "spelling" in prompt.lower()
    assert "punctuation" in prompt.lower()
    assert "same number of utterances" in prompt.lower()


def test_build_refinement_system_prompt_with_context():
    prompt = build_refinement_system_prompt(context="computer science lecture")
    assert "computer science lecture" in prompt


def test_build_refinement_user_prompt():
    utterances = [
        {"start": 0, "end": 5000, "speaker": "Speaker 1", "text": "Hello world"},
        {"start": 5000, "end": 10000, "speaker": "Speaker 2", "text": "Hi there"},
    ]
    prompt = build_refinement_user_prompt(utterances)
    assert "Hello world" in prompt
    assert "Hi there" in prompt
    parsed = json.loads(prompt)
    assert len(parsed) == 2


def test_chunk_utterances_for_refinement():
    utterances = [
        {"start": i * 1000, "end": (i + 1) * 1000, "speaker": "S1", "text": f"Utterance {i}"}
        for i in range(10)
    ]
    chunks = chunk_utterances_for_refinement(utterances, max_utterances=3)
    assert len(chunks) == 4  # 3+3+3+1
    assert len(chunks[0]) == 3
    assert len(chunks[3]) == 1
    all_utterances = [u for chunk in chunks for u in chunk]
    assert len(all_utterances) == 10
