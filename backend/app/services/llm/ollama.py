import json

import httpx

from app.config import settings
from app.metrics import track_llm_tokens
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import REFINEMENT_CONSOLIDATION_PROMPT


class OllamaProvider(LLMProvider):
    def __init__(self):
        self._base_url = settings.LLM_BASE_URL or "http://localhost:11434"
        self._model = settings.LLM_MODEL or "llama3"

    async def _chat(self, system: str, user: str, operation: str = "analysis") -> str:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            payload = response.json()
            track_llm_tokens("ollama", self._model, operation, payload)
            return payload["message"]["content"]

    async def _json_chat(self, system: str, user: str, operation: str) -> dict:
        return json.loads(await self._chat(system, user, operation))

    async def _consolidate_refinement_summaries(self, summaries: list[str]) -> str:
        return await self._chat(
            "You are a helpful assistant. Return only plain text, not JSON.",
            REFINEMENT_CONSOLIDATION_PROMPT.format(
                summaries="\n".join(f"- {s}" for s in summaries),
            ),
            operation="refinement",
        )

    async def generate_title(self, transcript: str) -> str:
        result = await self._chat(
            "Generate a short descriptive title (max 8 words) for the following transcript. Return ONLY the title text, nothing else. No quotes, no punctuation at the end.",
            transcript[:2000],
            operation="title",
        )
        try:
            data = json.loads(result)
            return str(data.get("title", data.get("text", result))).strip().strip('"\'')
        except (json.JSONDecodeError, AttributeError):
            return result.strip().strip('"\'')
