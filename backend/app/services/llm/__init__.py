from app.config import settings
from app.services.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider | None:
    if not settings.LLM_PROVIDER:
        return None
    if settings.LLM_PROVIDER == "ollama":
        from app.services.llm.ollama import OllamaProvider
        return OllamaProvider()
    else:
        from app.services.llm.openai import OpenAIProvider
        return OpenAIProvider()
