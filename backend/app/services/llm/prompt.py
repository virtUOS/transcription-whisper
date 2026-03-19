import json

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

Use speaker names when available. Respond ONLY with valid JSON matching this schema:
{schema}

Do not include any text outside the JSON object."""

def build_system_prompt(chapter_hints: list | None = None) -> str:
    prompt = SYSTEM_PROMPT.format(schema=json.dumps(SUMMARY_SCHEMA, indent=2))
    if chapter_hints:
        hint_lines = []
        for i, hint in enumerate(chapter_hints, 1):
            parts = []
            if hint.title:
                parts.append(f'Title: "{hint.title}"')
            if hint.description:
                parts.append(f'Description: "{hint.description}"')
            hint_lines.append(f"{i}. {' — '.join(parts)}")
        prompt += "\n\nThe user has provided the following chapter guidelines. Use these to guide your chapter segmentation. Match each hint to the relevant portion of the transcript. If a hint does not match any content in the recording, still include it as a chapter but explain in the summary field that this topic was not covered in the recording.\n\n" + "\n".join(hint_lines)
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

Consolidate these into a single summary with unified chapters. Respond ONLY with valid JSON matching the schema."""


CONSOLIDATION_PROMPT_WITH_HINTS = """You were given a long transcript split into chunks. Here are the summaries of each chunk:

{chunk_summaries}

The following chapter guidelines were provided by the user. Ensure each guideline appears exactly once in the final consolidated output, merging any duplicates from individual chunks.

{hint_text}

Consolidate these into a single summary with unified chapters. Respond ONLY with valid JSON matching the schema."""


def build_consolidation_prompt(chunk_summaries: str, chapter_hints: list | None = None) -> str:
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
        )
    return CONSOLIDATION_PROMPT.format(chunk_summaries=chunk_summaries)


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
Respond in the same language as the transcript.
Respond ONLY with valid JSON matching this schema:
{schema}

Do not include any text outside the JSON object."""


def build_protocol_system_prompt() -> str:
    return PROTOCOL_SYSTEM_PROMPT.format(schema=json.dumps(PROTOCOL_SCHEMA, indent=2))


def build_protocol_user_prompt(transcript: str, summary_context: str | None = None) -> str:
    prompt = f"Generate a meeting protocol from the following transcript:\n\n{transcript}"
    if summary_context:
        prompt += f"\n\nFor reference, here is an existing summary with chapters for this transcript:\n\n{summary_context}"
    return prompt


PROTOCOL_CONSOLIDATION_PROMPT = """You were given a long meeting transcript split into chunks. Here are the protocols of each chunk:

{chunk_protocols}

Consolidate these into a single meeting protocol. Merge duplicate participants, unify key points, decisions, and action items. Respond in the same language as the content above. Respond ONLY with valid JSON matching this schema:

{schema}"""
