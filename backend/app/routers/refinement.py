import json
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.dependencies import get_current_user
from app.models import (
    UserInfo, RefineRequest, LLMRefinementResponse, RefinementMetadata, RefinementResult, Utterance,
)
from app.database import get_db
from app.services.llm import get_llm_provider
from app.metrics import inc, observe, llm_requests_total, llm_duration_seconds, llm_errors_total, deletions_total, errors_total

router = APIRouter()


@router.post("/api/refine/{transcription_id}")
async def refine_transcription(
    transcription_id: str,
    body: RefineRequest | None = None,
    user: UserInfo = Depends(get_current_user),
):
    provider = get_llm_provider()
    if not provider:
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT status, result_json, refined_utterances_json, refinement_metadata_json
               FROM transcriptions WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        status, result_json, refined_json, metadata_json = row

        if metadata_json is not None:
            return RefinementResult(
                utterances=[Utterance(**u) for u in json.loads(refined_json)],
                metadata=RefinementMetadata(**json.loads(metadata_json)),
            )
        if refined_json is not None:
            raise HTTPException(status_code=429, detail="Refinement already in progress")

        if status != "completed":
            raise HTTPException(status_code=400, detail="Transcription not completed")

        original_utterances = json.loads(result_json or "[]")

        cursor = await db.execute(
            "SELECT original_label, custom_name FROM speaker_mappings WHERE transcription_id = ?",
            (transcription_id,),
        )
        mapping_rows = await cursor.fetchall()
        speaker_map = {r["original_label"]: r["custom_name"] for r in mapping_rows} if mapping_rows else {}

        await db.execute(
            "UPDATE transcriptions SET refined_utterances_json = '' WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        await db.commit()

    mapped_utterances = []
    for u in original_utterances:
        mapped = dict(u)
        if mapped.get("speaker") and mapped["speaker"] in speaker_map:
            mapped["speaker"] = speaker_map[mapped["speaker"]]
        mapped_utterances.append(mapped)

    context = body.context if body else None
    transcript_json = json.dumps(mapped_utterances, ensure_ascii=False)

    start_time = time.monotonic()
    try:
        llm_result: LLMRefinementResponse = await provider.generate_refinement(
            transcript_json, context=context,
        )
    except Exception:
        inc(llm_errors_total, settings.LLM_PROVIDER, settings.LLM_MODEL, "refinement")
        inc(errors_total, "llm_failed", "refinement")
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET refined_utterances_json = NULL WHERE id = ? AND user_id = ?",
                (transcription_id, user.id),
            )
            await db.commit()
        raise HTTPException(status_code=500, detail="Refinement failed")

    duration = time.monotonic() - start_time
    inc(llm_requests_total, settings.LLM_PROVIDER, settings.LLM_MODEL, "refinement")
    observe(llm_duration_seconds, duration, settings.LLM_PROVIDER, settings.LLM_MODEL, "refinement")

    if len(llm_result.utterances) != len(original_utterances):
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET refined_utterances_json = NULL WHERE id = ? AND user_id = ?",
                (transcription_id, user.id),
            )
            await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"LLM returned {len(llm_result.utterances)} utterances, expected {len(original_utterances)}",
        )

    changed_indices = []
    for i, (orig, refined) in enumerate(zip(original_utterances, llm_result.utterances)):
        if orig["text"] != refined.text:
            changed_indices.append(i)

    metadata = RefinementMetadata(
        changed_indices=changed_indices,
        changes_summary=llm_result.changes_summary,
        context=context,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    refined_data = [u.model_dump() for u in llm_result.utterances]

    async with get_db() as db:
        await db.execute(
            """UPDATE transcriptions
               SET refined_utterances_json = ?, refinement_metadata_json = ?
               WHERE id = ? AND user_id = ?""",
            (json.dumps(refined_data, ensure_ascii=False),
             json.dumps(metadata.model_dump(), ensure_ascii=False),
             transcription_id, user.id),
        )
        await db.commit()

    return RefinementResult(utterances=llm_result.utterances, metadata=metadata)


@router.get("/api/refine/{transcription_id}")
async def get_refinement(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT refined_utterances_json, refinement_metadata_json
               FROM transcriptions WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        result = await cursor.fetchone()

    if not result or not result["refinement_metadata_json"]:
        raise HTTPException(status_code=404, detail="No refinement found")

    return RefinementResult(
        utterances=[Utterance(**u) for u in json.loads(result["refined_utterances_json"])],
        metadata=RefinementMetadata(**json.loads(result["refinement_metadata_json"])),
    )


@router.delete("/api/refine/{transcription_id}")
async def delete_refinement(
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

        await db.execute(
            """UPDATE transcriptions
               SET refined_utterances_json = NULL, refinement_metadata_json = NULL
               WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        await db.commit()

    inc(deletions_total, "refinement")
    return {"status": "deleted"}
