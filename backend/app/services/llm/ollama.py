import json
import httpx
from app.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import build_system_prompt, build_user_prompt, chunk_transcript, CONSOLIDATION_PROMPT
from app.models import SummaryResult, SummaryChapter


class OllamaProvider(LLMProvider):
    def __init__(self):
        self._base_url = settings.LLM_BASE_URL or "http://localhost:11434"
        self._model = settings.LLM_MODEL or "llama3"

    async def generate_summary(self, transcript: str) -> SummaryResult:
        chunks = chunk_transcript(transcript)

        if len(chunks) == 1:
            return await self._summarize_single(chunks[0])

        chunk_summaries = []
        for chunk in chunks:
            result = await self._summarize_single(chunk)
            chunk_summaries.append(json.dumps(result.model_dump()))

        return await self._consolidate(chunk_summaries)

    async def _summarize_single(self, transcript: str) -> SummaryResult:
        content = await self._chat(build_system_prompt(), build_user_prompt(transcript))
        data = json.loads(content)
        return SummaryResult(
            summary=data.get("summary", ""),
            chapters=[SummaryChapter(**ch) for ch in data.get("chapters", [])],
        )

    async def _consolidate(self, chunk_summaries: list[str]) -> SummaryResult:
        prompt = CONSOLIDATION_PROMPT.format(
            chunk_summaries="\n\n---\n\n".join(chunk_summaries)
        )
        content = await self._chat(build_system_prompt(), prompt)
        data = json.loads(content)
        return SummaryResult(
            summary=data.get("summary", ""),
            chapters=[SummaryChapter(**ch) for ch in data.get("chapters", [])],
        )

    async def _chat(self, system: str, user: str) -> str:
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
            return response.json()["message"]["content"]
