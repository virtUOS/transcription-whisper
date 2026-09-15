import json
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


def test_refinement_prompt_defaults_to_leaving_utterances_alone():
    """The prompt must frame refinement as correction, not rewriting.

    A production run rewrote 215 of 248 utterances where an earlier run of the
    same transcript rewrote 62. The prompt asks only for spelling, punctuation
    and filler removal, so 87% was over-editing: every rule was phrased as an
    instruction to act, and restraint appeared only as an afterthought.
    """
    prompt = build_refinement_system_prompt().lower()
    assert "correction task, not a rewriting task" in prompt
    assert "leave an utterance exactly as received" in prompt
    assert "if you are unsure" in prompt


def test_refinement_prompt_protects_german_discourse_particles():
    """"also" and "quasi" are meaning-bearing German words, not filler.

    They were previously listed as filler words to remove, alongside genuine
    hesitation sounds. "also" is also an ordinary English word, so an unqualified
    instruction to strip it invites the model to delete meaning.
    """
    prompt = build_refinement_system_prompt()
    protect_line = next(
        line for line in prompt.splitlines() if "not noise" in line
    )
    for word in ("also", "quasi", "sozusagen", "eigentlich"):
        assert f'"{word}"' in protect_line, (
            f"{word} must be listed as protected, not as a word to strip"
        )
    assert "remove one only where it is unmistakably a hesitation" in protect_line


def test_refinement_prompt_preserves_spoken_register():
    prompt = build_refinement_system_prompt().lower()
    assert "do not rephrase" in prompt
    assert "colloquial phrasing, dialect and incomplete sentences" in prompt
