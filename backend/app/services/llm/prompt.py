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

def build_system_prompt() -> str:
    return SYSTEM_PROMPT.format(schema=json.dumps(SUMMARY_SCHEMA, indent=2))


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
