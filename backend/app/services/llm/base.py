import asyncio
import json
from abc import ABC, abstractmethod

# Parallel refinement requests per transcript. Chunks are independent, but this
# bounds how many a single long transcript can open against the LLM endpoint.
REFINEMENT_MAX_CONCURRENT = 4

from app.models import (
    SummaryResult, SummaryChapter,
    ProtocolResult, ProtocolKeyPoint, ProtocolDecision, ProtocolActionItem,
    LLMRefinementResponse, Utterance,
)
from app.services.llm.prompt import (
    build_system_prompt, build_user_prompt, chunk_transcript, build_consolidation_prompt,
    build_protocol_system_prompt, build_protocol_user_prompt,
    PROTOCOL_CONSOLIDATION_PROMPT, PROTOCOL_SCHEMA,
    build_refinement_system_prompt, build_refinement_user_prompt,
    chunk_utterances_for_refinement,
    _language_name,
)


class LLMProvider(ABC):
    @abstractmethod
    async def _json_chat(self, system: str, user: str, operation: str) -> dict:
        """Run a JSON-returning chat completion and return the parsed object."""

    @abstractmethod
    async def _consolidate_refinement_summaries(self, summaries: list[str]) -> str:
        """Collapse per-chunk refinement change-summaries into one plain-text string."""

    @abstractmethod
    async def generate_title(self, transcript: str) -> str:
        """Generate a short title from transcript text."""

    async def generate_summary(
        self, transcript: str, chapter_hints: list | None = None, language: str | None = None
    ) -> SummaryResult:
        chunks = chunk_transcript(transcript)
        system = build_system_prompt(chapter_hints, language)

        if len(chunks) == 1:
            data = await self._json_chat(system, build_user_prompt(chunks[0]), "analysis")
            return _parse_summary(data)

        chunk_summaries: list[str] = []
        for chunk in chunks:
            data = await self._json_chat(system, build_user_prompt(chunk), "analysis")
            chunk_summaries.append(json.dumps(data))

        prompt = build_consolidation_prompt(
            "\n\n---\n\n".join(chunk_summaries), chapter_hints, language,
        )
        data = await self._json_chat(system, prompt, "analysis")
        return _parse_summary(data)

    async def generate_protocol(
        self, transcript: str, summary_context: str | None = None, language: str | None = None
    ) -> ProtocolResult:
        chunks = chunk_transcript(transcript)
        system = build_protocol_system_prompt(language)

        if len(chunks) == 1:
            data = await self._json_chat(
                system, build_protocol_user_prompt(chunks[0], summary_context), "analysis",
            )
            return _parse_protocol(data)

        chunk_protocols: list[str] = []
        for chunk in chunks:
            data = await self._json_chat(
                system, build_protocol_user_prompt(chunk, summary_context), "analysis",
            )
            chunk_protocols.append(json.dumps(data))

        language_instruction = (
            f"Respond in {_language_name(language)}." if language
            else "Respond in the same language as the content above."
        )
        prompt = PROTOCOL_CONSOLIDATION_PROMPT.format(
            chunk_protocols="\n\n---\n\n".join(chunk_protocols),
            schema=json.dumps(PROTOCOL_SCHEMA, indent=2),
            language_instruction=language_instruction,
        )
        data = await self._json_chat(system, prompt, "analysis")
        return _parse_protocol(data)

    async def generate_refinement(
        self, transcript: str, context: str | None = None
    ) -> LLMRefinementResponse:
        utterances = json.loads(transcript)
        chunks = chunk_utterances_for_refinement(utterances)

        # Chunks are independent, so send them concurrently: run sequentially a
        # long transcript waits for the sum of every chunk's latency, which is
        # minutes. Bounded so a long transcript cannot open dozens of parallel
        # requests against the LLM endpoint at once.
        semaphore = asyncio.Semaphore(REFINEMENT_MAX_CONCURRENT)

        async def refine(chunk: list[dict]) -> dict:
            async with semaphore:
                return await self._json_chat(
                    build_refinement_system_prompt(context),
                    build_refinement_user_prompt(chunk),
                    "refinement",
                )

        # gather preserves input order, so utterances reassemble in transcript
        # order regardless of which chunk finishes first.
        results = await asyncio.gather(*(refine(chunk) for chunk in chunks))

        all_refined: list[dict] = []
        summaries: list[str] = []
        for data in results:
            all_refined.extend(data.get("utterances", []))
            summaries.append(data.get("changes_summary", ""))

        if len(summaries) > 1:
            combined_summary = await self._consolidate_refinement_summaries(summaries)
        else:
            combined_summary = summaries[0] if summaries else "No changes needed"

        return LLMRefinementResponse(
            utterances=[Utterance(**u) for u in all_refined],
            changes_summary=combined_summary,
        )


def reject_schema_echo(data):
    """Raise if the model returned the JSON schema instead of an instance of it.

    Some models answer a "respond with JSON matching this schema" prompt by
    echoing the schema back. The parsers below then find neither "summary" nor
    "chapters" and produce an empty result, so the user gets a blank analysis
    with no error recorded anywhere — the failure is invisible in logs and
    metrics alike. Detect it at the boundary and fail loudly instead.
    """
    if not isinstance(data, dict):
        return data
    if data.get("type") == "object" and isinstance(data.get("properties"), dict):
        raise ValueError(
            "The language model returned the JSON schema instead of a response "
            "matching it. Try again, or configure a different LLM_MODEL."
        )
    return data


def _parse_summary(data: dict) -> SummaryResult:
    return SummaryResult(
        summary=data.get("summary", ""),
        chapters=[SummaryChapter(**ch) for ch in data.get("chapters", [])],
    )


def _parse_protocol(data: dict) -> ProtocolResult:
    return ProtocolResult(
        title=data.get("title", ""),
        participants=data.get("participants", []),
        key_points=[ProtocolKeyPoint(**kp) for kp in data.get("key_points", [])],
        decisions=[ProtocolDecision(**d) for d in data.get("decisions", [])],
        action_items=[ProtocolActionItem(**ai) for ai in data.get("action_items", [])],
    )
