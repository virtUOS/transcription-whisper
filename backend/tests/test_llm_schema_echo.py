import pytest

from app.services.llm.base import reject_schema_echo


def test_accepts_a_normal_response():
    data = {"summary": "It happened.", "chapters": [{"title": "One"}]}
    assert reject_schema_echo(data) is data


def test_rejects_an_echoed_json_schema():
    """A model that returns the schema instead of filling it in used to reach the
    parsers, where .get("summary") and .get("chapters") both missed and the user
    silently received a blank analysis with no error anywhere."""
    echoed = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Overall summary"},
            "chapters": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["summary", "chapters"],
    }
    with pytest.raises(ValueError, match="schema"):
        reject_schema_echo(echoed)


def test_rejects_schema_echo_carrying_content_in_descriptions():
    """The deployed gemma-4-31B echoed the schema but wrote the real summary into
    the description fields, so a naive "is it the schema?" check on content alone
    would not catch it."""
    echoed = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "The meeting focused on KPIs..."},
        },
        "required": ["summary", "chapters"],
    }
    with pytest.raises(ValueError, match="schema"):
        reject_schema_echo(echoed)


def test_allows_a_response_that_merely_mentions_properties():
    data = {"summary": "We discussed object properties at length.", "chapters": []}
    assert reject_schema_echo(data) is data


def test_ignores_non_dict_input():
    assert reject_schema_echo([]) == []
