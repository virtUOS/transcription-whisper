import json

from openai import AsyncOpenAI

from app.config import settings
from app.metrics import track_llm_tokens
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import REFINEMENT_CONSOLIDATION_PROMPT


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL or None,
        )
        self._model = settings.LLM_MODEL or "gpt-4o"

    async def _json_chat(self, system: str, user: str, operation: str) -> dict:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        track_llm_tokens("openai", self._model, operation, getattr(response, "usage", None))
        return json.loads(response.choices[0].message.content or "{}")

    async def _consolidate_refinement_summaries(self, summaries: list[str]) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{
                "role": "user",
                "content": REFINEMENT_CONSOLIDATION_PROMPT.format(
                    summaries="\n".join(f"- {s}" for s in summaries),
                ),
            }],
            temperature=0.3,
        )
        track_llm_tokens("openai", self._model, "refinement", getattr(response, "usage", None))
        return (response.choices[0].message.content or "").strip()

    async def generate_title(self, transcript: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "Generate a short descriptive title (max 8 words) for the following transcript. Return ONLY the title text, nothing else. No quotes, no punctuation at the end."},
                {"role": "user", "content": transcript[:2000]},
            ],
            temperature=0.3,
        )
        track_llm_tokens("openai", self._model, "title", getattr(response, "usage", None))
        return (response.choices[0].message.content or "").strip().strip('"\'')
