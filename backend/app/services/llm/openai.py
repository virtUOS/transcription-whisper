import json
from openai import AsyncOpenAI
from app.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.prompt import (
    build_system_prompt, build_user_prompt, chunk_transcript, build_consolidation_prompt,
    build_protocol_system_prompt, build_protocol_user_prompt, PROTOCOL_CONSOLIDATION_PROMPT, PROTOCOL_SCHEMA,
    build_refinement_system_prompt, build_refinement_user_prompt, chunk_utterances_for_refinement,
    REFINEMENT_CONSOLIDATION_PROMPT,
)
from app.models import SummaryResult, SummaryChapter, ProtocolResult, ProtocolKeyPoint, ProtocolDecision, ProtocolActionItem, LLMRefinementResponse, Utterance


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL or None,
        )
        self._model = settings.LLM_MODEL or "gpt-4o"

    async def generate_summary(self, transcript: str, chapter_hints: list | None = None, language: str | None = None) -> SummaryResult:
        chunks = chunk_transcript(transcript)

        if len(chunks) == 1:
            return await self._summarize_single(chunks[0], chapter_hints, language)

        # Multi-chunk: summarize each, then consolidate
        chunk_summaries = []
        for chunk in chunks:
            result = await self._summarize_single(chunk, chapter_hints, language)
            chunk_summaries.append(json.dumps(result.model_dump()))

        return await self._consolidate(chunk_summaries, chapter_hints, language)

    async def _summarize_single(self, transcript: str, chapter_hints: list | None = None, language: str | None = None) -> SummaryResult:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_system_prompt(chapter_hints, language)},
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

    async def _consolidate(self, chunk_summaries: list[str], chapter_hints: list | None = None, language: str | None = None) -> SummaryResult:
        prompt = build_consolidation_prompt(
            "\n\n---\n\n".join(chunk_summaries), chapter_hints, language
        )
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_system_prompt(chapter_hints, language)},
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

    async def generate_protocol(self, transcript: str, summary_context: str | None = None, language: str | None = None) -> ProtocolResult:
        chunks = chunk_transcript(transcript)

        if len(chunks) == 1:
            return await self._protocol_single(chunks[0], summary_context, language)

        chunk_protocols = []
        for chunk in chunks:
            result = await self._protocol_single(chunk, summary_context, language)
            chunk_protocols.append(json.dumps(result.model_dump()))

        return await self._consolidate_protocol(chunk_protocols, language)

    async def _protocol_single(self, transcript: str, summary_context: str | None = None, language: str | None = None) -> ProtocolResult:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_protocol_system_prompt(language)},
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

    async def _consolidate_protocol(self, chunk_protocols: list[str], language: str | None = None) -> ProtocolResult:
        from app.services.llm.prompt import _language_name
        language_instruction = f"Respond in {_language_name(language)}." if language else "Respond in the same language as the content above."
        prompt = PROTOCOL_CONSOLIDATION_PROMPT.format(
            chunk_protocols="\n\n---\n\n".join(chunk_protocols),
            schema=json.dumps(PROTOCOL_SCHEMA, indent=2),
            language_instruction=language_instruction,
        )
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": build_protocol_system_prompt(language)},
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

    async def generate_refinement(self, transcript: str, context: str | None = None) -> LLMRefinementResponse:
        utterances = json.loads(transcript)
        chunks = chunk_utterances_for_refinement(utterances)

        all_refined: list[dict] = []
        summaries: list[str] = []

        for chunk in chunks:
            system = build_refinement_system_prompt(context)
            user = build_refinement_user_prompt(chunk)
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            all_refined.extend(data.get("utterances", []))
            summaries.append(data.get("changes_summary", ""))

        if len(summaries) > 1:
            consolidation_resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": REFINEMENT_CONSOLIDATION_PROMPT.format(
                    summaries="\n".join(f"- {s}" for s in summaries)
                )}],
                temperature=0.3,
            )
            combined_summary = (consolidation_resp.choices[0].message.content or "").strip()
        else:
            combined_summary = summaries[0] if summaries else "No changes needed"

        return LLMRefinementResponse(
            utterances=[Utterance(**u) for u in all_refined],
            changes_summary=combined_summary,
        )
