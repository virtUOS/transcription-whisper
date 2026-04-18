import hashlib
from typing import Literal, Sequence

SourceChoice = Literal["original", "refined"]


def hash_utterance_texts(utterances: Sequence[dict]) -> str:
    """SHA-256 hex of utterance text fields joined by \\n.

    Stable across speaker and timestamp edits; sensitive to text edits and
    to utterance order/insertion/deletion.
    """
    joined = "\n".join((u.get("text") or "") for u in utterances)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def select_source(
    *,
    explicit: SourceChoice | None,
    result_json: str | None,
    refined_json: str | None,
) -> SourceChoice:
    """Pick the source column to read.

    - Explicit 'refined' requires a non-empty refined_json (the '' sentinel
      means refinement is mid-run and does not count).
    - Explicit 'original' is always accepted.
    - When explicit is None, prefer 'refined' if available, else 'original'.
    Raises ValueError when 'refined' is requested without a refinement.
    """
    refined_available = bool(refined_json) and refined_json != ""
    if explicit == "refined":
        if not refined_available:
            raise ValueError("No refinement available for this transcription")
        return "refined"
    if explicit == "original":
        return "original"
    return "refined" if refined_available else "original"
