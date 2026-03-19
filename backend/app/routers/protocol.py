import json
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.dependencies import get_current_user
from app.models import UserInfo, ProtocolResult
from app.database import get_db
from app.services.llm import get_llm_provider
from app.services.llm.prompt import format_transcript_for_llm

router = APIRouter()


@router.post("/api/protocol/{transcription_id}", response_model=ProtocolResult)
async def generate_protocol(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    provider = get_llm_provider()
    if not provider:
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    async with get_db() as db:
        # Check for existing protocol
        cursor = await db.execute(
            "SELECT protocol_json, llm_provider, llm_model FROM protocols WHERE transcription_id = ?",
            (transcription_id,),
        )
        existing = await cursor.fetchone()
        if existing and existing["protocol_json"]:
            data = json.loads(existing["protocol_json"])
            data["llm_provider"] = existing["llm_provider"]
            data["llm_model"] = existing["llm_model"]
            return ProtocolResult(**data)

        # Rate limit: reject if protocol is already in progress
        if existing and not existing["protocol_json"]:
            raise HTTPException(status_code=429, detail="Protocol generation already in progress")

        # Get transcription
        cursor = await db.execute(
            "SELECT result_json FROM transcriptions WHERE id = ? AND user_id = ? AND status = 'completed'",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        result_json = row["result_json"]

        # Get speaker mappings
        cursor = await db.execute(
            "SELECT original_label, custom_name FROM speaker_mappings WHERE transcription_id = ?",
            (transcription_id,),
        )
        mapping_rows = await cursor.fetchall()
        speaker_map = {r["original_label"]: r["custom_name"] for r in mapping_rows} if mapping_rows else None

        # Optionally fetch existing summary as context
        summary_context = None
        cursor = await db.execute(
            "SELECT summary_json FROM summaries WHERE transcription_id = ?",
            (transcription_id,),
        )
        summary_row = await cursor.fetchone()
        if summary_row and summary_row["summary_json"]:
            summary_context = summary_row["summary_json"]

        # Insert placeholder row to mark generation as in-progress
        await db.execute(
            """INSERT OR IGNORE INTO protocols (transcription_id, protocol_json, llm_provider, llm_model)
               VALUES (?, NULL, ?, ?)""",
            (transcription_id, settings.LLM_PROVIDER, settings.LLM_MODEL),
        )
        await db.commit()

    utterances = json.loads(result_json or "[]")
    transcript = format_transcript_for_llm(utterances, speaker_map)

    try:
        result = await provider.generate_protocol(transcript, summary_context)
    except Exception:
        # Remove placeholder on failure so user can retry
        async with get_db() as db:
            await db.execute("DELETE FROM protocols WHERE transcription_id = ? AND protocol_json IS NULL", (transcription_id,))
            await db.commit()
        raise

    # Store completed protocol
    async with get_db() as db:
        await db.execute(
            """UPDATE protocols SET protocol_json = ?, llm_provider = ?, llm_model = ?
               WHERE transcription_id = ?""",
            (json.dumps(result.model_dump()), settings.LLM_PROVIDER, settings.LLM_MODEL, transcription_id),
        )
        await db.commit()

    result.llm_provider = settings.LLM_PROVIDER
    result.llm_model = settings.LLM_MODEL
    return result


@router.delete("/api/protocol/{transcription_id}")
async def delete_protocol(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Transcription not found")

        await db.execute("DELETE FROM protocols WHERE transcription_id = ?", (transcription_id,))
        await db.commit()

    return {"status": "deleted"}
