import json
import httpx
from app.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import (
    build_system_prompt, build_user_prompt, chunk_transcript, build_consolidation_prompt,
    build_protocol_system_prompt, build_protocol_user_prompt, PROTOCOL_CONSOLIDATION_PROMPT, PROTOCOL_SCHEMA,
)
from app.models import SummaryResult, SummaryChapter, ProtocolResult, ProtocolKeyPoint, ProtocolDecision, ProtocolActionItem


class OllamaProvider(LLMProvider):
    def __init__(self):
        self._base_url = settings.LLM_BASE_URL or "http://localhost:11434"
        self._model = settings.LLM_MODEL or "llama3"

    async def generate_summary(self, transcript: str, chapter_hints: list | None = None) -> SummaryResult:
        chunks = chunk_transcript(transcript)

        if len(chunks) == 1:
            return await self._summarize_single(chunks[0], chapter_hints)

        chunk_summaries = []
        for chunk in chunks:
            result = await self._summarize_single(chunk, chapter_hints)
            chunk_summaries.append(json.dumps(result.model_dump()))

        return await self._consolidate(chunk_summaries, chapter_hints)

    async def _summarize_single(self, transcript: str, chapter_hints: list | None = None) -> SummaryResult:
        content = await self._chat(build_system_prompt(chapter_hints), build_user_prompt(transcript))
        data = json.loads(content)
        return SummaryResult(
            summary=data.get("summary", ""),
            chapters=[SummaryChapter(**ch) for ch in data.get("chapters", [])],
        )

    async def _consolidate(self, chunk_summaries: list[str], chapter_hints: list | None = None) -> SummaryResult:
        prompt = build_consolidation_prompt(
            "\n\n---\n\n".join(chunk_summaries), chapter_hints
        )
        content = await self._chat(build_system_prompt(chapter_hints), prompt)
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
        content = await self._chat(build_protocol_system_prompt(), build_protocol_user_prompt(transcript, summary_context))
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
        content = await self._chat(build_protocol_system_prompt(), prompt)
        data = json.loads(content)
        return ProtocolResult(
            title=data.get("title", ""),
            participants=data.get("participants", []),
            key_points=[ProtocolKeyPoint(**kp) for kp in data.get("key_points", [])],
            decisions=[ProtocolDecision(**d) for d in data.get("decisions", [])],
            action_items=[ProtocolActionItem(**ai) for ai in data.get("action_items", [])],
        )
