import json

LANGUAGE_NAMES = {
    "de": "German", "en": "English", "fr": "French", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
    "ru": "Russian", "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
    "ar": "Arabic", "hi": "Hindi", "tr": "Turkish", "sv": "Swedish",
    "da": "Danish", "fi": "Finnish", "el": "Greek", "he": "Hebrew",
    "hu": "Hungarian", "cs": "Czech", "ro": "Romanian", "uk": "Ukrainian",
}


def _language_name(code: str) -> str:
    """Convert ISO language code to full name for LLM prompts."""
    return LANGUAGE_NAMES.get(code, code)

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "Overall summary, 1-3 paragraphs"},
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {"type": "integer", "description": "Start time in milliseconds"},
                    "end_time": {"type": "integer", "description": "End time in milliseconds"},
                    "summary": {"type": "string", "description": "Brief description of this chapter"},
                },
                "required": ["title", "start_time", "end_time", "summary"],
            },
        },
    },
    "required": ["summary", "chapters"],
}

SYSTEM_PROMPT = """You are a transcript summarizer. Given a timestamped transcript, produce:
1. An overall summary (1-3 paragraphs)
2. Chapters based on topic shifts, each with a title, start/end timestamps (in milliseconds), and a brief description

Use speaker names when available.
{language_instruction}Respond ONLY with valid JSON matching this schema:
{schema}

Do not include any text outside the JSON object."""

def build_system_prompt(chapter_hints: list | None = None, language: str | None = None) -> str:
    if language:
        language_instruction = f"Respond in {_language_name(language)}.\n"
    else:
        language_instruction = "Respond in the same language as the transcript.\n"
    prompt = SYSTEM_PROMPT.format(
        schema=json.dumps(SUMMARY_SCHEMA, indent=2),
        language_instruction=language_instruction,
    )
    if chapter_hints:
        hint_lines = []
        for i, hint in enumerate(chapter_hints, 1):
            parts = []
            if hint.title:
                parts.append(f'Title: "{hint.title}"')
            if hint.description:
                parts.append(f'Description: "{hint.description}"')
            hint_lines.append(f"{i}. {' — '.join(parts)}")
        prompt += "\n\nThe user has provided the following chapter guidelines. Use these to guide your chapter segmentation. Match each hint to the relevant portion of the transcript. If a hint does not match any content in the recording, still include it as a chapter with start_time and end_time both set to 0, and explain in the summary field that this topic was not covered in the recording.\n\n" + "\n".join(hint_lines)
    return prompt


def build_user_prompt(transcript: str) -> str:
    return f"Summarize the following transcript into chapters:\n\n{transcript}"


def format_transcript_for_llm(utterances: list[dict], speaker_mappings: dict[str, str] | None = None) -> str:
    """Format utterances into a timestamped transcript string for the LLM."""
    lines = []
    for utt in utterances:
        start_s = utt["start"] / 1000
        m, s = divmod(int(start_s), 60)
        h, m = divmod(m, 60)
        timestamp = f"[{h:02d}:{m:02d}:{s:02d}]"

        speaker = utt.get("speaker", "")
        if speaker and speaker_mappings:
            speaker = speaker_mappings.get(speaker, speaker)

        if speaker:
            lines.append(f"{timestamp} {speaker}: {utt['text']}")
        else:
            lines.append(f"{timestamp} {utt['text']}")

    return "\n".join(lines)


def chunk_transcript(transcript: str, max_chars: int = 100_000) -> list[str]:
    """Split transcript into chunks that fit within context limits.
    Tries to break at paragraph/speaker boundaries."""
    if len(transcript) <= max_chars:
        return [transcript]

    chunks = []
    lines = transcript.split("\n")
    current_chunk: list[str] = []
    current_len = 0

    for line in lines:
        if current_len + len(line) > max_chars and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(line)
        current_len += len(line) + 1

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


CONSOLIDATION_PROMPT = """You were given a long transcript split into chunks. Here are the summaries of each chunk:

{chunk_summaries}

Consolidate these into a single summary with unified chapters. {language_instruction}Respond ONLY with valid JSON matching the schema."""


CONSOLIDATION_PROMPT_WITH_HINTS = """You were given a long transcript split into chunks. Here are the summaries of each chunk:

{chunk_summaries}

The following chapter guidelines were provided by the user. Ensure each guideline appears exactly once in the final consolidated output, merging any duplicates from individual chunks.

{hint_text}

Consolidate these into a single summary with unified chapters. {language_instruction}Respond ONLY with valid JSON matching the schema."""


def build_consolidation_prompt(chunk_summaries: str, chapter_hints: list | None = None, language: str | None = None) -> str:
    if language:
        language_instruction = f"Respond in {_language_name(language)}. "
    else:
        language_instruction = "Respond in the same language as the content above. "
    if chapter_hints:
        hint_lines = []
        for i, hint in enumerate(chapter_hints, 1):
            parts = []
            if hint.title:
                parts.append(f'Title: "{hint.title}"')
            if hint.description:
                parts.append(f'Description: "{hint.description}"')
            hint_lines.append(f"{i}. {' — '.join(parts)}")
        return CONSOLIDATION_PROMPT_WITH_HINTS.format(
            chunk_summaries=chunk_summaries,
            hint_text="\n".join(hint_lines),
            language_instruction=language_instruction,
        )
    return CONSOLIDATION_PROMPT.format(chunk_summaries=chunk_summaries, language_instruction=language_instruction)


PROTOCOL_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Meeting title inferred from context"},
        "participants": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Speaker names from the transcript",
        },
        "key_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "speaker": {"type": "string"},
                    "timestamp": {
                        "type": ["integer", "null"],
                        "description": "Start time in milliseconds, null if not determinable",
                    },
                    "content": {"type": "string"},
                },
                "required": ["topic", "speaker", "timestamp", "content"],
            },
        },
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "decision": {"type": "string"},
                    "timestamp": {
                        "type": ["integer", "null"],
                        "description": "Time in milliseconds, null if not determinable",
                    },
                },
                "required": ["decision", "timestamp"],
            },
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "assignee": {"type": "string"},
                    "timestamp": {
                        "type": ["integer", "null"],
                        "description": "Time in milliseconds, null if not determinable",
                    },
                },
                "required": ["task", "assignee", "timestamp"],
            },
        },
    },
    "required": ["title", "participants", "key_points", "decisions", "action_items"],
}

PROTOCOL_SYSTEM_PROMPT = """You are a meeting protocol generator. Given a timestamped transcript of a meeting, produce a structured protocol with:
1. A meeting title inferred from context
2. A list of participants (from speaker labels; use "Unknown Speaker" if no speaker labels are present)
3. Key discussion points attributed to speakers with timestamps
4. Decisions made during the meeting
5. Action items with assignees

Use speaker names exactly as they appear in the transcript. If no speaker labels are present, use "Unknown Speaker" for all attributions.
{language_instruction}
Respond ONLY with valid JSON matching this schema:
{schema}

Do not include any text outside the JSON object."""


def build_protocol_system_prompt(language: str | None = None) -> str:
    if language:
        language_instruction = f"Respond in {_language_name(language)}."
    else:
        language_instruction = "Respond in the same language as the transcript."
    return PROTOCOL_SYSTEM_PROMPT.format(
        schema=json.dumps(PROTOCOL_SCHEMA, indent=2),
        language_instruction=language_instruction,
    )


def build_protocol_user_prompt(transcript: str, summary_context: str | None = None) -> str:
    prompt = f"Generate a meeting protocol from the following transcript:\n\n{transcript}"
    if summary_context:
        prompt += f"\n\nFor reference, here is an existing summary with chapters for this transcript:\n\n{summary_context}"
    return prompt


PROTOCOL_CONSOLIDATION_PROMPT = """You were given a long meeting transcript split into chunks. Here are the protocols of each chunk:

{chunk_protocols}

Consolidate these into a single meeting protocol. Merge duplicate participants, unify key points, decisions, and action items. {language_instruction} Respond ONLY with valid JSON matching this schema:

{schema}"""


REFINEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "utterances": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "speaker": {"type": ["string", "null"]},
                    "text": {"type": "string"},
                },
                "required": ["start", "end", "text"],
            },
        },
        "changes_summary": {"type": "string"},
    },
    "required": ["utterances", "changes_summary"],
}

REFINEMENT_SYSTEM_PROMPT = """You are a transcription refinement assistant. You receive a JSON array of utterances from an automatic speech recognition (ASR) system and must return a corrected version.

This is a correction task, not a rewriting task. The speaker's own wording is
the source of truth. Leave an utterance exactly as received unless it contains a
specific, identifiable error from the list below. Most utterances in a good ASR
transcript need no change at all; returning them untouched is the expected
outcome, not a failure to do your job.

Correct only these:
- Clear spelling and punctuation errors
- Obvious grammar errors that are transcription artefacts rather than how the speaker actually spoke
- Inconsistent terminology and proper nouns (e.g. if "Fourier" appears as "fourier", "four year", use the correct form consistently)
- Non-lexical hesitation sounds: uh, um, er, äh, ähm, hm
- False starts and self-corrections where the speaker audibly restarts ("the the", "we went — we drove to")

Never do these:
- Do NOT remove ordinary words that carry meaning or tone. In particular "also", "quasi", "sozusagen", "eigentlich", "ja", "halt" and "genau" are normal German words, not noise — remove one only where it is unmistakably a hesitation, never by default
- Do NOT rephrase, condense, modernise or improve wording that is already correct
- Do NOT convert spoken register into written register — colloquial phrasing, dialect and incomplete sentences are how people speak and must survive
- Do NOT change timestamps (start, end) — return them exactly as received
- Do NOT change speaker labels — return them exactly as received
- Do NOT add, invent, or remove substantive content
- Return EXACTLY the same number of utterances in the same order

If you are unsure whether something is an error, leave it unchanged.

Return a changes_summary string describing what you changed at a high level (e.g. "Fixed 3 punctuation errors, normalized 'Fourier' spelling across 2 utterances, removed 4 hesitation sounds"). If nothing needed changing, set changes_summary to "No changes needed".

Return valid JSON matching this schema:
{schema}"""

REFINEMENT_CONTEXT_ADDENDUM = """
Additional context provided by the user to guide your corrections:
{context}

Use this context to better identify domain-specific terminology, proper nouns, and technical terms."""


def build_refinement_system_prompt(context: str | None = None) -> str:
    prompt = REFINEMENT_SYSTEM_PROMPT.format(schema=json.dumps(REFINEMENT_SCHEMA, indent=2))
    if context:
        prompt += REFINEMENT_CONTEXT_ADDENDUM.format(context=context)
    return prompt


def build_refinement_user_prompt(utterances: list[dict]) -> str:
    return json.dumps(utterances, ensure_ascii=False)


# Refinement and translation echo the chunk back, so output is bounded by input:
# real 50-utterance chunks measured 2275-3615 completion tokens. Nothing in the
# request said so, and vLLM serves the model with --max-model-len 262144, so a
# chunk that fails to stop generates until it hits the context window. Eleven
# requests on the deployed endpoint finished with reason "length", the same
# eleven that exceeded 600s; six emitted over 200k tokens. At 79 tok/s that is
# 21 minutes, which no chunk size can rescue because the runaway is unrelated to
# input size. 16384 clears the largest measured chunk 4x over while turning a
# runaway into a fast, retryable failure instead of ten GPU-minutes taken from
# every other tenant of the shared endpoint.
REFINEMENT_OUTPUT_TOKEN_CAP = 16384


def chunk_utterances_for_refinement(
    # Refinement returns every utterance rewritten, so output size — and
    # therefore latency — scales with the chunk. At roughly 178 tok/s a
    # 50-utterance chunk takes about 79s; 200 needed over 300s and timed out.
    utterances: list[dict], max_utterances: int = 50
) -> list[list[dict]]:
    if len(utterances) <= max_utterances:
        return [utterances]
    chunks = []
    for i in range(0, len(utterances), max_utterances):
        chunks.append(utterances[i:i + max_utterances])
    return chunks


REFINEMENT_CONSOLIDATION_PROMPT = """You received multiple changes_summary strings from refining different chunks of the same transcript. Combine them into a single concise summary.

Individual summaries:
{summaries}

Return a single combined summary string (not JSON, just the text)."""


TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {
        "utterances": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "speaker": {"type": ["string", "null"]},
                    "text": {"type": "string"},
                },
                "required": ["start", "end", "text"],
            },
        },
    },
    "required": ["utterances"],
}

TRANSLATION_SYSTEM_PROMPT = """You are a subtitle translator. Given a timestamped transcript, translate all text to {target_language}.

Rules:
- Translate the text field of each utterance to {target_language}
- Preserve the exact timestamps (start, end) without modification
- Preserve speaker labels exactly as they are
- Preserve meaning, tone, and technical terms
- Return the SAME number of utterances in the SAME order
- Do not merge or split utterances

{language_instruction}Respond ONLY with valid JSON matching this schema:
{schema}

Do not include any text outside the JSON object."""


def build_translation_system_prompt(target_language: str) -> str:
    lang_name = _language_name(target_language)
    return TRANSLATION_SYSTEM_PROMPT.format(
        target_language=lang_name,
        language_instruction=f"Respond in {lang_name}.\n",
        schema=json.dumps(TRANSLATION_SCHEMA, indent=2),
    )


def build_translation_user_prompt(utterances: list[dict]) -> str:
    return json.dumps(utterances, ensure_ascii=False)


ANALYSIS_TEMPLATES = {
    "summary": {
        "name": "Summary with chapters",
        "description": "Overall summary with chapter breakdown",
        "system_prompt": SYSTEM_PROMPT,
        "schema": SUMMARY_SCHEMA,
    },
    "protocol": {
        "name": "Meeting protocol",
        "description": "Structured meeting notes with key points, decisions, and action items",
        "system_prompt": PROTOCOL_SYSTEM_PROMPT,
        "schema": PROTOCOL_SCHEMA,
    },
    "agenda": {
        "name": "Agenda-based notes",
        "description": "Notes structured around a provided agenda",
        "system_prompt": """You are a meeting note generator. Given a timestamped transcript and an agenda, produce structured notes following the agenda items.

For each agenda item, summarize what was discussed, any decisions made, and action items.

{language_instruction}The agenda:
{agenda}

Respond ONLY with valid JSON matching this schema:
{schema}

Do not include any text outside the JSON object.""",
        "schema": SUMMARY_SCHEMA,
    },
}


def list_analysis_templates() -> list[dict]:
    return [
        {"id": k, "name": v["name"], "description": v["description"], "default_prompt": v["system_prompt"]}
        for k, v in ANALYSIS_TEMPLATES.items()
    ]


def build_analysis_system_prompt(
    template_name: str | None = None,
    custom_prompt: str | None = None,
    language: str | None = None,
    chapter_hints: list | None = None,
    agenda: str | None = None,
) -> tuple[str, dict]:
    """Build the system prompt and schema for an analysis request.
    Returns (system_prompt, json_schema)."""
    language_instruction = f"Respond in {_language_name(language)}.\n" if language else ""

    if custom_prompt:
        # User provided a custom prompt — use it with a flexible schema
        prompt = custom_prompt
        if language_instruction:
            prompt = language_instruction + prompt
        # For custom prompts, use a permissive schema
        schema = {"type": "object"}
        return prompt, schema

    template = ANALYSIS_TEMPLATES.get(template_name or "summary")
    if not template:
        template = ANALYSIS_TEMPLATES["summary"]

    system_prompt = template["system_prompt"]
    schema = template["schema"]

    # Handle template-specific formatting
    if template_name == "agenda":
        # Route on the template, not on whether agenda text was supplied: the
        # prompt carries a literal {agenda} placeholder either way, so falling
        # through to the generic .format() below raises KeyError.
        system_prompt = system_prompt.format(
            language_instruction=language_instruction,
            agenda=agenda or "No agenda was supplied. Infer the agenda items from the transcript itself.",
            schema=json.dumps(schema, indent=2),
        )
    elif template_name == "summary":
        # Reuse existing summary prompt builder logic
        return build_system_prompt(chapter_hints, language), schema
    elif template_name == "protocol":
        return build_protocol_system_prompt(language), schema
    else:
        # format_map with a defaulting lookup so a template that gains a new
        # placeholder degrades to an empty value instead of raising KeyError
        # and surfacing as a 500.
        class _Defaults(dict):
            def __missing__(self, key):
                return ""

        system_prompt = system_prompt.format_map(_Defaults(
            language_instruction=language_instruction,
            schema=json.dumps(schema, indent=2),
        ))

    return system_prompt, schema
