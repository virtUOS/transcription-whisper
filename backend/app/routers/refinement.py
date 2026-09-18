import json
import logging
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.dependencies import get_current_user
from app.router_helpers import (
    ensure_transcription_owned,
    load_speaker_mappings,
    reset_refinement_state,
)
from app.models import (
    UserInfo, RefineRequest, LLMRefinementResponse, RefinementMetadata, RefinementResult, Utterance,
)
from app.database import get_db
from app.services.llm import get_llm_provider
from app.metrics import inc, measure_llm_operation, deletions_total

router = APIRouter()

# Transcription ids with a retry in flight. In-process on purpose: the app
# runs one uvicorn worker (Dockerfile ENTRYPOINT sets no --workers), so this
# set is authoritative, clears itself on restart, and leaves the stored
# partial intact if the process dies mid-retry. The DB sentinel the initial
# run uses ('' in refined_utterances_json) would instead orphan the row, and
# nulling the metadata as a lock would make GET 404 on a reload mid-retry.
# Revisit if the app ever runs more than one worker.
_retries_in_flight: set[str] = set()


async def _load_mapped_utterances(db, transcription_id: str, result_json: str | None) -> list[dict]:
    """Original utterances with the user's speaker names applied — what the LLM is sent.

    Shared by the initial refinement and the retry so both send the model the
    same text for the same utterance.
    """
    speaker_map = await load_speaker_mappings(db, transcription_id)
    mapped = []
    for u in json.loads(result_json or "[]"):
        m = dict(u)
        if m.get("speaker") and m["speaker"] in speaker_map:
            m["speaker"] = speaker_map[m["speaker"]]
        mapped.append(m)
    return mapped


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
        mapped_utterances = await _load_mapped_utterances(db, transcription_id, result_json)

        await db.execute(
            "UPDATE transcriptions SET refined_utterances_json = '' WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        await db.commit()

    context = body.context if body else None
    transcript_json = json.dumps(mapped_utterances, ensure_ascii=False)

    try:
        async with measure_llm_operation("refinement"):
            llm_result: LLMRefinementResponse = await provider.generate_refinement(
                transcript_json, context=context,
            )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            "Refinement failed for transcription %s: %s: %s",
            transcription_id, type(e).__name__, e,
        )
        logging.error("Traceback: %s", traceback.format_exc())
        await reset_refinement_state(transcription_id, user.id)
        raise HTTPException(status_code=500, detail="Refinement failed")

    if len(llm_result.utterances) != len(original_utterances):
        await reset_refinement_state(transcription_id, user.id)
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
        failed_ranges=llm_result.failed_ranges,
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


@router.post("/api/refine/{transcription_id}/retry")
async def retry_failed_refinement_chunks(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    """Re-run refinement on the ranges the last run reported as failed.

    The stored partial is the source of truth: only ranges that recover are
    spliced in, the context is reused from the saved metadata, and a range
    that fails again simply stays in failed_ranges for another attempt.
    """
    provider = get_llm_provider()
    if not provider:
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT result_json, refined_utterances_json, refinement_metadata_json
               FROM transcriptions WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row or not row["refinement_metadata_json"]:
            raise HTTPException(status_code=404, detail="No refinement found")

        metadata = RefinementMetadata(**json.loads(row["refinement_metadata_json"]))
        if not metadata.failed_ranges:
            raise HTTPException(status_code=400, detail="Nothing to retry")

        original_utterances = json.loads(row["result_json"] or "[]")
        refined = json.loads(row["refined_utterances_json"])
        mapped_utterances = await _load_mapped_utterances(db, transcription_id, row["result_json"])

    if transcription_id in _retries_in_flight:
        raise HTTPException(status_code=409, detail="Retry already in progress")
    _retries_in_flight.add(transcription_id)
    try:
        try:
            async with measure_llm_operation("refinement"):
                llm_result: LLMRefinementResponse = await provider.generate_refinement(
                    json.dumps(mapped_utterances, ensure_ascii=False),
                    context=metadata.context,
                    ranges=metadata.failed_ranges,
                    previous_summary=metadata.changes_summary,
                )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                "Refinement retry failed for transcription %s: %s: %s",
                transcription_id, type(e).__name__, e,
            )
            raise HTTPException(status_code=500, detail="Refinement retry failed")

        still_failed = set(llm_result.failed_ranges)
        new_utterances = [u.model_dump() for u in llm_result.utterances]
        for a, b in metadata.failed_ranges:
            if (a, b) not in still_failed:
                refined[a:b] = new_utterances[a:b]

        updated = metadata.model_copy(update={
            "changed_indices": [
                i for i, (orig, ref) in enumerate(zip(original_utterances, refined))
                if orig["text"] != ref["text"]
            ],
            "changes_summary": llm_result.changes_summary,
            "failed_ranges": llm_result.failed_ranges,
        })

        async with get_db() as db:
            # The IS NOT NULL predicate makes this a no-op if the user deleted
            # the refinement while the retry was running.
            await db.execute(
                """UPDATE transcriptions
                   SET refined_utterances_json = ?, refinement_metadata_json = ?
                   WHERE id = ? AND user_id = ? AND refinement_metadata_json IS NOT NULL""",
                (json.dumps(refined, ensure_ascii=False),
                 json.dumps(updated.model_dump(), ensure_ascii=False),
                 transcription_id, user.id),
            )
            await db.commit()
    finally:
        _retries_in_flight.discard(transcription_id)

    return RefinementResult(utterances=[Utterance(**u) for u in refined], metadata=updated)


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
        await ensure_transcription_owned(db, transcription_id, user.id)

        await db.execute(
            """UPDATE transcriptions
               SET refined_utterances_json = NULL, refinement_metadata_json = NULL
               WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        await db.commit()

    inc(deletions_total, "refinement")
    return {"status": "deleted"}
