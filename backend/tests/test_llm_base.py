import pytest
from app.services.llm.base import LLMProvider


def test_llm_provider_is_abstract():
    with pytest.raises(TypeError):
        LLMProvider()


def test_llm_provider_has_generate_protocol():
    assert hasattr(LLMProvider, "generate_protocol")
