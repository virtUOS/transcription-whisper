import json
import time
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.dependencies import get_current_user
from app.models import UserInfo, SummaryResult, SummaryChapter, SummarizeRequest
from app.database import get_db
from app.services.llm import get_llm_provider
from app.services.llm.prompt import format_transcript_for_llm
from app.metrics import inc, observe, llm_requests_total, llm_duration_seconds, llm_errors_total, deletions_total, errors_total

router = APIRouter()


@router.post("/api/summarize/{transcription_id}", response_model=SummaryResult)
async def generate_summary(
    transcription_id: str,
    body: SummarizeRequest | None = None,
    user: UserInfo = Depends(get_current_user),
):
    provider = get_llm_provider()
    if not provider:
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    async with get_db() as db:
        # Check for existing summary
        cursor = await db.execute(
            "SELECT summary_json, llm_provider, llm_model FROM summaries WHERE transcription_id = ?",
            (transcription_id,),
        )
        existing = await cursor.fetchone()

        chapter_hints = body.chapter_hints if body and body.chapter_hints else None

        if existing and existing["summary_json"]:
            data = json.loads(existing["summary_json"])
            # Only invalidate cache if hints were explicitly provided and differ
            if body is not None and body.chapter_hints is not None:
                existing_hints = data.get("chapter_hints")
                new_hints_serialized = [h.model_dump() for h in chapter_hints] if chapter_hints else None
                if existing_hints != new_hints_serialized:
                    # Hints differ — delete cached summary to regenerate
                    await db.execute("DELETE FROM summaries WHERE transcription_id = ?", (transcription_id,))
                    await db.commit()
                else:
                    data["llm_provider"] = existing["llm_provider"]
                    data["llm_model"] = existing["llm_model"]
                    return SummaryResult(**data)
            else:
                # No body or no hints provided — return cached result
                data["llm_provider"] = existing["llm_provider"]
                data["llm_model"] = existing["llm_model"]
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

        result_json = row["result_json"]

        # Get speaker mappings
        cursor = await db.execute(
            "SELECT original_label, custom_name FROM speaker_mappings WHERE transcription_id = ?",
            (transcription_id,),
        )
        mapping_rows = await cursor.fetchall()
        speaker_map = {r["original_label"]: r["custom_name"] for r in mapping_rows} if mapping_rows else None

        # Insert placeholder row to mark generation as in-progress (enables 429 rate limiting)
        await db.execute(
            """INSERT OR IGNORE INTO summaries (transcription_id, summary_json, llm_provider, llm_model)
               VALUES (?, NULL, ?, ?)""",
            (transcription_id, settings.LLM_PROVIDER, settings.LLM_MODEL),
        )
        await db.commit()

    utterances = json.loads(result_json or "[]")
    transcript = format_transcript_for_llm(utterances, speaker_map)

    start_time = time.monotonic()
    try:
        result = await provider.generate_summary(transcript, chapter_hints)
    except Exception:
        inc(llm_errors_total, settings.LLM_PROVIDER, settings.LLM_MODEL, "summary")
        inc(errors_total, "llm_failed", "summary")
        # Remove placeholder on failure so user can retry
        async with get_db() as db:
            await db.execute("DELETE FROM summaries WHERE transcription_id = ? AND summary_json IS NULL", (transcription_id,))
            await db.commit()
        raise

    duration = time.monotonic() - start_time
    inc(llm_requests_total, settings.LLM_PROVIDER, settings.LLM_MODEL, "summary")
    observe(llm_duration_seconds, duration, settings.LLM_PROVIDER, settings.LLM_MODEL, "summary")

    result.chapter_hints = chapter_hints

    # Store completed summary
    async with get_db() as db:
        await db.execute(
            """UPDATE summaries SET summary_json = ?, llm_provider = ?, llm_model = ?
               WHERE transcription_id = ?""",
            (json.dumps(result.model_dump()), settings.LLM_PROVIDER, settings.LLM_MODEL, transcription_id),
        )
        await db.commit()

    result.llm_provider = settings.LLM_PROVIDER
    result.llm_model = settings.LLM_MODEL
    return result


@router.delete("/api/summarize/{transcription_id}/chapters/{chapter_index}")
async def delete_chapter(
    transcription_id: str,
    chapter_index: int,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Transcription not found")

        cursor = await db.execute(
            "SELECT summary_json, llm_provider, llm_model FROM summaries WHERE transcription_id = ?",
            (transcription_id,),
        )
        row = await cursor.fetchone()
        if not row or not row["summary_json"]:
            raise HTTPException(status_code=404, detail="Summary not found")

        data = json.loads(row["summary_json"])
        chapters = data.get("chapters", [])
        if chapter_index < 0 or chapter_index >= len(chapters):
            raise HTTPException(status_code=404, detail="Chapter not found")

        chapters.pop(chapter_index)
        data["chapters"] = chapters

        await db.execute(
            "UPDATE summaries SET summary_json = ? WHERE transcription_id = ?",
            (json.dumps(data), transcription_id),
        )
        await db.commit()

    data["llm_provider"] = row["llm_provider"]
    data["llm_model"] = row["llm_model"]
    return SummaryResult(**data)


@router.delete("/api/summarize/{transcription_id}")
async def delete_summary(
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

        await db.execute("DELETE FROM summaries WHERE transcription_id = ?", (transcription_id,))
        await db.commit()

    inc(deletions_total, "summary")

    return {"status": "deleted"}
