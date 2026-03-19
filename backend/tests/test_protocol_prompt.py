import json
from app.services.llm.prompt import (
    PROTOCOL_SCHEMA,
    build_protocol_system_prompt,
    build_protocol_user_prompt,
    PROTOCOL_CONSOLIDATION_PROMPT,
)


def test_protocol_schema_has_required_fields():
    required = PROTOCOL_SCHEMA["required"]
    assert "title" in required
    assert "participants" in required
    assert "key_points" in required
    assert "decisions" in required
    assert "action_items" in required


def test_build_protocol_system_prompt_includes_schema():
    prompt = build_protocol_system_prompt()
    assert "key_points" in prompt
    assert "action_items" in prompt
    assert "JSON" in prompt


def test_build_protocol_user_prompt_without_context():
    prompt = build_protocol_user_prompt("[00:00:00] Speaker 1: Hello")
    assert "[00:00:00] Speaker 1: Hello" in prompt
    assert "summary" not in prompt.lower() or "reference" not in prompt.lower()


def test_build_protocol_user_prompt_with_summary_context():
    context = json.dumps({"summary": "Test", "chapters": []})
    prompt = build_protocol_user_prompt("[00:00:00] Speaker 1: Hello", summary_context=context)
    assert "reference" in prompt.lower()
    assert context in prompt


def test_protocol_consolidation_prompt_has_placeholders():
    assert "{chunk_protocols}" in PROTOCOL_CONSOLIDATION_PROMPT
    assert "{schema}" in PROTOCOL_CONSOLIDATION_PROMPT
