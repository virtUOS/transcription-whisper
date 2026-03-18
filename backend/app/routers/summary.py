import json
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.dependencies import get_current_user
from app.models import UserInfo, SummaryResult
from app.database import get_db
from app.services.llm import get_llm_provider
from app.services.llm.prompt import format_transcript_for_llm

router = APIRouter()


@router.post("/api/summarize/{transcription_id}", response_model=SummaryResult)
async def generate_summary(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    provider = get_llm_provider()
    if not provider:
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    async with get_db() as db:
        # Check for existing summary
        cursor = await db.execute(
            "SELECT summary_json FROM summaries WHERE transcription_id = ?",
            (transcription_id,),
        )
        existing = await cursor.fetchone()
        if existing and existing["summary_json"]:
            data = json.loads(existing["summary_json"])
            return SummaryResult(**data)

        # Rate limit: reject if summary is already in progress
        if existing and not existing["summary_json"]:
            raise HTTPException(status_code=429, detail="Summary generation already in progress")

        # Get transcription
        cursor = await db.execute(
            "SELECT result_json FROM transcriptions WHERE id = ? AND user_id = ? AND status = 'completed'",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        # Get speaker mappings
        cursor = await db.execute(
            "SELECT original_label, custom_name FROM speaker_mappings WHERE transcription_id = ?",
            (transcription_id,),
        )
        mapping_rows = await cursor.fetchall()
        speaker_map = {r["original_label"]: r["custom_name"] for r in mapping_rows} if mapping_rows else None

    utterances = json.loads(row["result_json"] or "[]")
    transcript = format_transcript_for_llm(utterances, speaker_map)

    # Insert placeholder row to mark generation as in-progress (enables 429 rate limiting)
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO summaries (transcription_id, summary_json, llm_provider, llm_model)
               VALUES (?, NULL, ?, ?)""",
            (transcription_id, settings.LLM_PROVIDER, settings.LLM_MODEL),
        )
        await db.commit()

    try:
        result = await provider.generate_summary(transcript)
    except Exception:
        # Remove placeholder on failure so user can retry
        async with get_db() as db:
            await db.execute("DELETE FROM summaries WHERE transcription_id = ? AND summary_json IS NULL", (transcription_id,))
            await db.commit()
        raise

    # Store completed summary
    async with get_db() as db:
        await db.execute(
            """UPDATE summaries SET summary_json = ?, llm_provider = ?, llm_model = ?
               WHERE transcription_id = ?""",
            (json.dumps(result.model_dump()), settings.LLM_PROVIDER, settings.LLM_MODEL, transcription_id),
        )
        await db.commit()

    return result
