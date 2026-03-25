import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from app.config import settings
from app.dependencies import get_current_user
from app.models import (
    UserInfo, TranscriptionSettings as TranscriptionSettingsModel,
    TranscriptionStatus, TranscriptionListItem, Utterance, SpeakerMappingRequest,
)
from app.database import get_db
from app.services.asr import get_asr_backend
from app.services.asr.base import TranscriptionSettings
from app.services.formats import generate_srt, generate_vtt, generate_txt
from app.metrics import (
    inc, observe, gauge_inc, gauge_dec,
    transcriptions_total, transcription_duration_seconds, active_transcriptions,
    diarization_speakers_detected, edits_saved_total, speaker_renames_total,
    downloads_total, deletions_total, errors_total,
    websocket_connections_active, websocket_connections_total,
)

router = APIRouter()


@router.post("/api/transcribe")
async def start_transcription(
    req: TranscriptionSettingsModel,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, mp3_path FROM files WHERE id = ? AND user_id = ?",
            (req.file_id, user.id),
        )
        file_row = await cursor.fetchone()
        if not file_row:
            raise HTTPException(status_code=404, detail="File not found")

    transcription_id = str(uuid.uuid4())
    mp3_path = file_row["mp3_path"]

    async with get_db() as db:
        await db.execute(
            """INSERT INTO transcriptions
               (id, user_id, file_id, asr_backend, status, language, model,
                min_speakers, max_speakers, initial_prompt, hotwords)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (transcription_id, user.id, req.file_id, settings.ASR_BACKEND,
             "pending", req.language, req.model, req.min_speakers, req.max_speakers,
             req.initial_prompt, req.hotwords),
        )
        await db.commit()

    asyncio.create_task(_run_transcription(transcription_id, mp3_path, req))
    return {"id": transcription_id, "status": "pending"}


async def _run_transcription(transcription_id: str, file_path: str, req: TranscriptionSettingsModel):
    backend = get_asr_backend()
    ts = TranscriptionSettings(
        language=req.language, model=req.model,
        min_speakers=req.min_speakers, max_speakers=req.max_speakers,
        initial_prompt=req.initial_prompt, hotwords=req.hotwords,
    )

    gauge_inc(active_transcriptions)
    start_time = time.monotonic()

    try:
        async with get_db() as db:
            await db.execute("UPDATE transcriptions SET status = ? WHERE id = ?", ("processing", transcription_id))
            await db.commit()

        asr_job_id = await backend.submit(file_path, ts)

        async with get_db() as db:
            await db.execute("UPDATE transcriptions SET asr_job_id = ? WHERE id = ?", (asr_job_id, transcription_id))
            await db.commit()

        while True:
            status = await backend.get_status(asr_job_id)
            if status.status == "completed":
                break
            elif status.status == "failed":
                raise RuntimeError(status.error or "Transcription failed")
            await asyncio.sleep(5)

        result = await backend.get_result(asr_job_id)

        duration = time.monotonic() - start_time
        observe(transcription_duration_seconds, duration, req.language or "auto", req.model or "default")
        inc(transcriptions_total, req.language or "auto", req.model or "default", "completed")

        # Track number of unique speakers detected
        speakers = {u.speaker for u in result.utterances if u.speaker}
        if speakers:
            observe(diarization_speakers_detected, len(speakers))

        async with get_db() as db:
            await db.execute(
                """UPDATE transcriptions SET status = ?, result_json = ?, completed_at = ? WHERE id = ?""",
                ("completed", json.dumps([u.model_dump() for u in result.utterances]),
                 datetime.now(timezone.utc).isoformat(), transcription_id),
            )
            await db.commit()

    except Exception as e:
        inc(transcriptions_total, req.language or "auto", req.model or "default", "failed")
        inc(errors_total, "transcription_failed", "asr")

        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET status = ?, error_message = ? WHERE id = ?",
                ("failed", str(e), transcription_id),
            )
            await db.commit()
    finally:
        gauge_dec(active_transcriptions)


@router.get("/api/status/{transcription_id}")
async def get_status(transcription_id: str, user: UserInfo = Depends(get_current_user)):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, status, error_message FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return TranscriptionStatus(id=row["id"], status=row["status"], error=row["error_message"])


@router.get("/api/transcription/{transcription_id}")
async def get_transcription(transcription_id: str, user: UserInfo = Depends(get_current_user)):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Transcription not found")
    if row["status"] != "completed":
        raise HTTPException(status_code=400, detail="Transcription not yet completed")

    utterances = [Utterance(**u) for u in json.loads(row["result_json"] or "[]")]

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT original_label, custom_name FROM speaker_mappings WHERE transcription_id = ?",
            (transcription_id,),
        )
        mapping_rows = await cursor.fetchall()
        speaker_mappings = {r["original_label"]: r["custom_name"] for r in mapping_rows} if mapping_rows else {}

        cursor = await db.execute(
            "SELECT protocol_json FROM protocols WHERE transcription_id = ?",
            (transcription_id,),
        )
        protocol_row = await cursor.fetchone()
        protocol = json.loads(protocol_row["protocol_json"]) if protocol_row and protocol_row["protocol_json"] else None

    return {
        "id": row["id"], "status": row["status"],
        "utterances": [u.model_dump() for u in utterances],
        "text": " ".join(u.text for u in utterances),
        "language": row["language"],
        "speaker_mappings": speaker_mappings,
        "protocol": protocol,
    }


@router.get("/api/transcription/{transcription_id}/export/{format_type}")
async def export_transcription(transcription_id: str, format_type: str, user: UserInfo = Depends(get_current_user)):
    if format_type not in ("txt", "srt", "vtt", "json"):
        raise HTTPException(status_code=400, detail="Invalid format")

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT result_json FROM transcriptions WHERE id = ? AND user_id = ? AND status = 'completed'",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        cursor = await db.execute(
            "SELECT original_label, custom_name FROM speaker_mappings WHERE transcription_id = ?",
            (transcription_id,),
        )
        mapping_rows = await cursor.fetchall()
        speaker_map = {r["original_label"]: r["custom_name"] for r in mapping_rows} if mapping_rows else None

    utterances = [Utterance(**u) for u in json.loads(row["result_json"] or "[]")]

    if format_type == "srt":
        content = generate_srt(utterances, speaker_map)
        media_type = "text/srt"
    elif format_type == "vtt":
        content = generate_vtt(utterances, speaker_map)
        media_type = "text/vtt"
    elif format_type == "txt":
        content = generate_txt(utterances, speaker_map)
        media_type = "text/plain"
    else:
        content = json.dumps([u.model_dump() for u in utterances], indent=2)
        media_type = "application/json"

    inc(downloads_total, format_type)

    from fastapi.responses import Response
    return Response(content=content, media_type=media_type)


@router.put("/api/transcription/{transcription_id}")
async def update_transcription(transcription_id: str, utterances: list[Utterance], user: UserInfo = Depends(get_current_user)):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM transcriptions WHERE id = ? AND user_id = ? AND status = 'completed'",
            (transcription_id, user.id),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Transcription not found")

        await db.execute(
            "UPDATE transcriptions SET result_json = ? WHERE id = ?",
            (json.dumps([u.model_dump() for u in utterances]), transcription_id),
        )
        await db.commit()

    inc(edits_saved_total)

    return {"status": "ok"}


@router.put("/api/transcription/{transcription_id}/speakers")
async def update_speaker_mappings(transcription_id: str, request: SpeakerMappingRequest, user: UserInfo = Depends(get_current_user)):
    mappings = request.mappings
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Transcription not found")

        await db.execute("DELETE FROM speaker_mappings WHERE transcription_id = ?", (transcription_id,))
        for original, custom in mappings.items():
            await db.execute(
                "INSERT INTO speaker_mappings (transcription_id, original_label, custom_name) VALUES (?, ?, ?)",
                (transcription_id, original, custom),
            )
        await db.commit()

    inc(speaker_renames_total)

    return {"status": "ok"}


@router.delete("/api/transcription/{transcription_id}")
async def delete_transcription(transcription_id: str, user: UserInfo = Depends(get_current_user)):
    import os
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT file_id FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        # Get file paths before deleting DB records
        file_id = row["file_id"]
        file_cursor = await db.execute(
            "SELECT file_path, mp3_path FROM files WHERE id = ?", (file_id,),
        )
        file_row = await file_cursor.fetchone()

        await db.execute("DELETE FROM protocols WHERE transcription_id = ?", (transcription_id,))
        await db.execute("DELETE FROM speaker_mappings WHERE transcription_id = ?", (transcription_id,))
        await db.execute("DELETE FROM transcriptions WHERE id = ?", (transcription_id,))
        await db.execute("DELETE FROM files WHERE id = ?", (file_id,))
        await db.commit()

    # Remove files from disk
    if file_row:
        for path in (file_row["file_path"], file_row["mp3_path"]):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass

    inc(deletions_total, "transcription")

    return {"status": "deleted"}


@router.get("/api/transcriptions")
async def list_transcriptions(user: UserInfo = Depends(get_current_user)):
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT t.id, t.file_id, f.original_filename, t.status, t.language, t.model, t.created_at, f.file_size
               FROM transcriptions t
               JOIN files f ON t.file_id = f.id
               WHERE t.user_id = ?
               ORDER BY t.created_at DESC""",
            (user.id,),
        )
        rows = await cursor.fetchall()

    return [
        TranscriptionListItem(
            id=r["id"], file_id=r["file_id"], original_filename=r["original_filename"],
            status=r["status"], language=r["language"], model=r["model"],
            created_at=r["created_at"], file_size=r["file_size"],
        ).model_dump()
        for r in rows
    ]


@router.websocket("/api/ws/status/{transcription_id}")
async def websocket_status(websocket: WebSocket, transcription_id: str):
    await websocket.accept()
    inc(websocket_connections_total)
    gauge_inc(websocket_connections_active)
    try:
        # Extract user from headers (same as get_current_user dependency)
        user_id = websocket.headers.get("x-forwarded-user", "anonymous")

        # Verify user owns this transcription
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id FROM transcriptions WHERE id = ? AND user_id = ?",
                (transcription_id, user_id),
            )
            if not await cursor.fetchone():
                await websocket.close(code=4003, reason="Not found")
                return

        while True:
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT status, error_message FROM transcriptions WHERE id = ?",
                    (transcription_id,),
                )
                row = await cursor.fetchone()

            if not row:
                await websocket.send_json({"type": "error", "detail": "Transcription not found"})
                break

            status = row["status"]
            msg = {"type": "status", "status": status}
            if status == "failed" and row["error_message"]:
                msg["error"] = row["error_message"]
            await websocket.send_json(msg)

            if status in ("completed", "failed"):
                break

            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    finally:
        gauge_dec(websocket_connections_active)
        try:
            await websocket.close()
        except Exception:
            pass
