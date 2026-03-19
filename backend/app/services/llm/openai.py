import json
from openai import AsyncOpenAI
from app.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import (
    build_system_prompt, build_user_prompt, chunk_transcript, CONSOLIDATION_PROMPT,
    build_protocol_system_prompt, build_protocol_user_prompt, PROTOCOL_CONSOLIDATION_PROMPT, PROTOCOL_SCHEMA,
)
from app.models import SummaryResult, SummaryChapter, ProtocolResult, ProtocolKeyPoint, ProtocolDecision, ProtocolActionItem


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

    async def generate_protocol(self, transcript: str, summary_context: str | None = None) -> ProtocolResult:
        chunks = chunk_transcript(transcript)

        if len(chunks) == 1:
            return await self._protocol_single(chunks[0], summary_context)

        chunk_protocols = []
        for chunk in chunks:
            result = await self._protocol_single(chunk, summary_context)
            chunk_protocols.append(json.dumps(result.model_dump()))

        return await self._consolidate_protocol(chunk_protocols)

    async def _protocol_single(self, transcript: str, summary_context: str | None = None) -> ProtocolResult:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_protocol_system_prompt()},
                {"role": "user", "content": build_protocol_user_prompt(transcript, summary_context)},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return ProtocolResult(
            title=data.get("title", ""),
            participants=data.get("participants", []),
            key_points=[ProtocolKeyPoint(**kp) for kp in data.get("key_points", [])],
            decisions=[ProtocolDecision(**d) for d in data.get("decisions", [])],
            action_items=[ProtocolActionItem(**ai) for ai in data.get("action_items", [])],
        )

    async def _consolidate_protocol(self, chunk_protocols: list[str]) -> ProtocolResult:
        prompt = PROTOCOL_CONSOLIDATION_PROMPT.format(
            chunk_protocols="\n\n---\n\n".join(chunk_protocols),
            schema=json.dumps(PROTOCOL_SCHEMA, indent=2),
        )
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_protocol_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        return ProtocolResult(
            title=data.get("title", ""),
            participants=data.get("participants", []),
            key_points=[ProtocolKeyPoint(**kp) for kp in data.get("key_points", [])],
            decisions=[ProtocolDecision(**d) for d in data.get("decisions", [])],
            action_items=[ProtocolActionItem(**ai) for ai in data.get("action_items", [])],
        )
