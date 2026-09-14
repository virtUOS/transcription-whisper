from app.services.llm.prompt import ANALYSIS_TEMPLATES, build_analysis_system_prompt


def test_every_template_builds_without_agenda_text():
    """Every template must build even when no agenda text is supplied.

    The agenda template's prompt contains a literal {agenda} placeholder. When
    the user picks that template but leaves the agenda field empty, the builder
    used to fall through to a .format() call that did not pass `agenda`, raising
    KeyError and surfacing as a 500 from POST /api/analysis/{id}.
    """
    for name in ANALYSIS_TEMPLATES:
        prompt, schema = build_analysis_system_prompt(template_name=name)
        assert prompt
        assert isinstance(schema, dict)


def test_agenda_template_without_agenda_text():
    prompt, _ = build_analysis_system_prompt(template_name="agenda", agenda=None)
    assert prompt
    assert "{agenda}" not in prompt


def test_agenda_template_with_empty_agenda_text():
    prompt, _ = build_analysis_system_prompt(template_name="agenda", agenda="")
    assert prompt
    assert "{agenda}" not in prompt


def test_agenda_template_with_agenda_text_includes_it():
    prompt, _ = build_analysis_system_prompt(
        template_name="agenda", agenda="1. Budget\n2. Hiring"
    )
    assert "1. Budget" in prompt
    assert "{agenda}" not in prompt


def test_unknown_template_falls_back_to_summary():
    prompt, schema = build_analysis_system_prompt(template_name="does-not-exist")
    assert prompt
    assert isinstance(schema, dict)
