import json
from openai import AsyncOpenAI
from app.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import build_system_prompt, build_user_prompt, chunk_transcript, CONSOLIDATION_PROMPT
from app.models import SummaryResult, SummaryChapter


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL or None,
        )
        self._model = settings.LLM_MODEL or "gpt-4o"

    async def generate_summary(self, transcript: str) -> SummaryResult:
        chunks = chunk_transcript(transcript)

        if len(chunks) == 1:
            return await self._summarize_single(chunks[0])

        # Multi-chunk: summarize each, then consolidate
        chunk_summaries = []
        for chunk in chunks:
            result = await self._summarize_single(chunk)
            chunk_summaries.append(json.dumps(result.model_dump()))

        return await self._consolidate(chunk_summaries)

    async def _summarize_single(self, transcript: str) -> SummaryResult:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": build_user_prompt(transcript)},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return SummaryResult(
            summary=data.get("summary", ""),
            chapters=[SummaryChapter(**ch) for ch in data.get("chapters", [])],
        )

    async def _consolidate(self, chunk_summaries: list[str]) -> SummaryResult:
        prompt = CONSOLIDATION_PROMPT.format(
            chunk_summaries="\n\n---\n\n".join(chunk_summaries)
        )
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return SummaryResult(
            summary=data.get("summary", ""),
            chapters=[SummaryChapter(**ch) for ch in data.get("chapters", [])],
        )
