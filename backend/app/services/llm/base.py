import asyncio
import json
import logging
from abc import ABC, abstractmethod

from app.config import settings
from app.models import (
    SummaryResult, SummaryChapter,
    ProtocolResult, ProtocolKeyPoint, ProtocolDecision, ProtocolActionItem,
    LLMRefinementResponse, Utterance,
)
from app.services.llm.prompt import (
    build_system_prompt, build_user_prompt, chunk_transcript, build_consolidation_prompt,
    build_protocol_system_prompt, build_protocol_user_prompt,
    PROTOCOL_CONSOLIDATION_PROMPT, PROTOCOL_SCHEMA,
    build_refinement_system_prompt,
    REFINEMENT_OUTPUT_TOKEN_CAP,
    chunk_utterances_for_refinement,
    _language_name,
)

# Parallel chunk requests per transcript, for the operations that rewrite every
# utterance (refinement and translation). See config.LLM_CHUNK_CONCURRENCY for
# why this is deliberately small.
LLM_CHUNK_MAX_CONCURRENT = settings.LLM_CHUNK_CONCURRENCY

# Re-attempts for a single chunk that comes back with the wrong number of
# utterances. Cheap compared with discarding every other chunk's work.
CHUNK_COUNT_RETRIES = 2

# Re-attempts for a chunk whose request failed outright — a timeout, a dropped
# connection, a transient endpoint error. The shared endpoint's latency varies
# widely: the same 50-utterance chunk was measured at 108s and at 237s against a
# 360s timeout, so a slow draw is a dice roll rather than a broken request. A
# long transcript rolls those dice once per chunk (1489 utterances is 30 chunks),
# and without this a single unlucky draw discards every other chunk's work.
CHUNK_ERROR_RETRIES = 2


async def chunked_utterance_call(
    provider: "LLMProvider",
    utterances: list[dict],
    build_system,
    operation: str,
    expect_same_count: bool = False,
    tolerate_failures: bool = False,
    chunks: list[list[dict]] | None = None,
) -> list[dict | None]:
    """Send utterances to the LLM in chunks, concurrently, in input order.

    Shared by the operations that rewrite every utterance — refinement and
    translation. Both make the model echo the whole chunk back, so latency
    scales with chunk size and a sequential loop waits for the sum of every
    chunk. Each of these grew its own copy of this logic, and each copy had to
    be fixed separately for chunk size, concurrency and schema-echo handling.

    `build_system` is called per chunk to produce the system prompt. Results
    come back in input order, so callers can concatenate them directly.

    `chunks`, when given, is sent as-is instead of chunking `utterances`; the
    refinement retry passes exactly the ranges that failed before.

    `tolerate_failures` makes a chunk that exhausts its retries resolve to None
    in its slot instead of raising and cancelling its siblings. Refinement opts
    in because an unrefined range is still correct text; translation must not,
    because an untranslated range is not.
    """
    if chunks is None:
        chunks = chunk_utterances_for_refinement(utterances)
    semaphore = asyncio.Semaphore(LLM_CHUNK_MAX_CONCURRENT)

    async def _attempt(chunk: list[dict]) -> dict:
        """One request for one chunk, retried if the request itself fails.

        Finishing slowly is preferred over failing fast here: the user is
        already waiting minutes and would rather wait longer than lose the
        whole job to one slow chunk.
        """
        for attempt in range(CHUNK_ERROR_RETRIES + 1):
            try:
                async with semaphore:
                    return await provider._json_chat(
                        build_system(),
                        json.dumps(chunk, ensure_ascii=False),
                        operation,
                        max_tokens=REFINEMENT_OUTPUT_TOKEN_CAP,
                    )
            except asyncio.CancelledError:
                # A sibling chunk failed and we are being torn down; never
                # swallow this into a retry.
                raise
            except Exception as e:
                if attempt == CHUNK_ERROR_RETRIES:
                    raise
                logging.warning(
                    "%s chunk request failed (%s: %s), retrying (attempt %d/%d)",
                    operation, type(e).__name__, e, attempt + 1,
                    CHUNK_ERROR_RETRIES + 1,
                )
        raise AssertionError("unreachable")

    async def one(chunk: list[dict]) -> dict:
        # Refinement and translation must return one utterance per input, but
        # models do not honour that reliably — one short chunk used to discard
        # every other chunk's work and surface as a 500 after several minutes.
        # Retry just the offending chunk instead.
        last_count = None
        for attempt in range(CHUNK_COUNT_RETRIES + 1):
            data = await _attempt(chunk)
            if not expect_same_count:
                return data
            last_count = len(data.get("utterances", []))
            if last_count == len(chunk):
                return data
            logging.warning(
                "%s chunk returned %d utterances, expected %d (attempt %d/%d)",
                operation, last_count, len(chunk), attempt + 1, CHUNK_COUNT_RETRIES + 1,
            )
        raise ValueError(
            f"The language model returned {last_count} utterances for a chunk of "
            f"{len(chunk)} after {CHUNK_COUNT_RETRIES + 1} attempts."
        )

    async def one_or_none(chunk: list[dict]) -> dict | None:
        try:
            return await one(chunk)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.warning(
                "%s chunk of %d utterances gave up after retries (%s: %s); keeping original text",
                operation, len(chunk), type(e).__name__, e,
            )
            return None

    # gather preserves input order, so utterances reassemble in transcript order
    # regardless of which chunk finishes first. On failure, cancel the siblings
    # rather than leaving them generating into a job nobody is waiting for —
    # unless the caller tolerates failures, in which case a dead chunk is a
    # None slot and the siblings finish.
    runner = one_or_none if tolerate_failures else one
    tasks = [asyncio.ensure_future(runner(chunk)) for chunk in chunks]
    try:
        return list(await asyncio.gather(*tasks))
    except BaseException:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


class LLMProvider(ABC):
    @abstractmethod
    async def _json_chat(
        self, system: str, user: str, operation: str, max_tokens: int | None = None
    ) -> dict:
        """Run a JSON-returning chat completion and return the parsed object.

        `max_tokens` bounds the reply. The utterance paths pass it because their
        output is bounded by their input; analysis leaves it None because a
        consolidation is not, and a cap sized for a chunk would truncate it.
        """

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
        results = await chunked_utterance_call(
            self, utterances,
            build_system=lambda: build_refinement_system_prompt(context),
            operation="refinement",
            expect_same_count=True,
        )

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
