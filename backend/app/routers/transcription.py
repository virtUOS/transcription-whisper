import asyncio
import json
import logging
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from app.config import settings
from app.dependencies import get_current_user
from app.router_helpers import ensure_transcription_owned, load_speaker_mappings
from app.models import (
    UserInfo, TranscriptionSettings as TranscriptionSettingsModel,
    TranscriptionStatus, TranscriptionListItem, Utterance, SpeakerMappingRequest,
    TitleRequest,
)
from app.database import get_db
from app.services.asr import get_asr_backend
from app.services.api_tokens import resolve_token
from app.services.asr.base import TranscriptionSettings
from app.services.audio import get_media_duration
from app.services.formats import generate_srt, generate_vtt, generate_txt
from app.metrics import (
    inc, observe, gauge_inc, gauge_dec,
    transcriptions_total, transcription_duration_seconds, active_transcriptions,
    transcription_audio_duration_seconds, transcription_realtime_factor,
    transcription_queue_depth, transcription_queue_wait_seconds,
    diarization_speakers_detected, edits_saved_total, speaker_renames_total,
    downloads_total, deletions_total, errors_total,
    websocket_connections_active, websocket_connections_total,
    websocket_messages_sent_total, websocket_disconnects_total,
    auth_failures_total, api_token_auth_total,
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

    gauge_inc(transcription_queue_depth)
    submitted_at = time.monotonic()
    asyncio.create_task(_run_transcription(transcription_id, mp3_path, req, submitted_at))
    return {"id": transcription_id, "status": "pending"}


async def _run_transcription(transcription_id: str, file_path: str, req: TranscriptionSettingsModel, submitted_at: float):
    backend = get_asr_backend()
    backend_name = settings.ASR_BACKEND
    ts = TranscriptionSettings(
        language=req.language, model=req.model,
        min_speakers=req.min_speakers, max_speakers=req.max_speakers,
        initial_prompt=req.initial_prompt, hotwords=req.hotwords,
    )

    gauge_dec(transcription_queue_depth)
    observe(transcription_queue_wait_seconds, time.monotonic() - submitted_at, backend_name)
    gauge_inc(active_transcriptions)
    start_time = time.monotonic()

    try:
        audio_duration = await asyncio.wait_for(get_media_duration(file_path), timeout=5)
    except (asyncio.TimeoutError, Exception):
        audio_duration = None
    if audio_duration is not None:
        observe(transcription_audio_duration_seconds, audio_duration, backend_name)

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
        lang_label = req.language or "auto"
        model_label = req.model or "default"
        observe(transcription_duration_seconds, duration, backend_name, lang_label, model_label)
        inc(transcriptions_total, backend_name, lang_label, model_label, "completed")
        if audio_duration and audio_duration > 0:
            observe(transcription_realtime_factor, duration / audio_duration, backend_name, model_label)

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

        # Generate title if LLM is available
        try:
            from app.services.llm import get_llm_provider
            provider = get_llm_provider()
            if provider and result.utterances:
                transcript_text = " ".join(u.text for u in result.utterances)
                title = await provider.generate_title(transcript_text)
                if title:
                    async with get_db() as db:
                        await db.execute(
                            "UPDATE transcriptions SET title = ? WHERE id = ?",
                            (title, transcription_id),
                        )
                        await db.commit()
        except Exception as e:
            logging.warning("Title generation failed for %s: %s", transcription_id, e)

    except Exception as e:
        logging.error("Transcription %s failed: %s: %s", transcription_id, type(e).__name__, e)
        logging.error("Traceback: %s", traceback.format_exc())
        inc(transcriptions_total, backend_name, req.language or "auto", req.model or "default", "failed")
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
        speaker_mappings = await load_speaker_mappings(db, transcription_id)

    return {
        "id": row["id"], "status": row["status"],
        "utterances": [u.model_dump() for u in utterances],
        "text": " ".join(u.text for u in utterances),
        "language": row["language"],
        "speaker_mappings": speaker_mappings,
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

        speaker_map = await load_speaker_mappings(db, transcription_id)

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
        await ensure_transcription_owned(db, transcription_id, user.id)

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

        await db.execute("DELETE FROM analyses WHERE transcription_id = ?", (transcription_id,))
        await db.execute("DELETE FROM speaker_mappings WHERE transcription_id = ?", (transcription_id,))
        await db.execute("DELETE FROM transcriptions WHERE id = ?", (transcription_id,))

        # Only delete the file if no other transcriptions reference it
        other = await db.execute(
            "SELECT 1 FROM transcriptions WHERE file_id = ? LIMIT 1", (file_id,),
        )
        if not await other.fetchone():
            await db.execute("DELETE FROM files WHERE id = ?", (file_id,))
            should_delete_files = True
        else:
            should_delete_files = False
        await db.commit()

    # Remove files from disk only if the file record was deleted
    if file_row and should_delete_files:
        for path in (file_row["file_path"], file_row["mp3_path"]):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass

    inc(deletions_total, "transcription")

    return {"status": "deleted"}


@router.post("/api/transcription/{transcription_id}/archive")
async def archive_transcription(transcription_id: str, user: UserInfo = Depends(get_current_user)):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT file_id FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        expires_at = (datetime.now(timezone.utc) + timedelta(hours=settings.ARCHIVE_EXPIRY_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            "UPDATE files SET expires_at = ?, is_archived = 1 WHERE id = ?",
            (expires_at, row["file_id"]),
        )
        await db.commit()

    return {"status": "archived", "expires_at": expires_at}


@router.get("/api/transcriptions")
async def list_transcriptions(user: UserInfo = Depends(get_current_user)):
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT t.id, t.file_id, f.original_filename, t.status, t.language, t.model, t.created_at, f.file_size, f.expires_at, f.is_archived, t.title, f.has_video
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
            expires_at=r["expires_at"], archived=bool(r["is_archived"]),
            title=r["title"], has_video=bool(r["has_video"] or 0),
        ).model_dump()
        for r in rows
    ]


@router.patch("/api/transcription/{transcription_id}/title")
async def update_title(transcription_id: str, body: TitleRequest, user: UserInfo = Depends(get_current_user)):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Not found")
        await db.execute(
            "UPDATE transcriptions SET title = ? WHERE id = ?",
            (body.title, transcription_id),
        )
        await db.commit()
    return {"status": "ok"}


@router.websocket("/api/ws/status/{transcription_id}")
async def websocket_status(websocket: WebSocket, transcription_id: str):
    await websocket.accept()
    inc(websocket_connections_total)
    gauge_inc(websocket_connections_active)
    close_reason = "client_disconnect"
    try:
        # Prefer API token from query param when feature is enabled
        user_id: str | None = None
        if settings.ENABLE_API_TOKENS:
            raw = websocket.query_params.get("token")
            if raw and raw.startswith("tw_"):
                async with get_db() as db:
                    result = await resolve_token(db, raw_token=raw)
                if result is None:
                    inc(api_token_auth_total, "failure")
                    inc(auth_failures_total, "invalid_token")
                    close_reason = "auth_missing"
                    await websocket.close(code=4001, reason="Invalid token")
                    return
                user_id = result[0].id
                inc(api_token_auth_total, "success")

        if user_id is None:
            user_id = websocket.headers.get("x-auth-request-user")

        if not user_id:
            inc(auth_failures_total, "ws_missing_headers")
            close_reason = "auth_missing"
            await websocket.close(code=4001, reason="Missing authentication")
            return

        # Verify user owns this transcription
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id FROM transcriptions WHERE id = ? AND user_id = ?",
                (transcription_id, user_id),
            )
            if not await cursor.fetchone():
                close_reason = "not_found"
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
                inc(websocket_messages_sent_total, "error")
                close_reason = "not_found_record"
                break

            status = row["status"]
            msg = {"type": "status", "status": status}
            if status == "failed" and row["error_message"]:
                msg["error"] = row["error_message"]
            await websocket.send_json(msg)
            inc(websocket_messages_sent_total, "status")

            if status in ("completed", "failed"):
                close_reason = status
                break

            await asyncio.sleep(5)
    except WebSocketDisconnect:
        close_reason = "client_disconnect"
    except Exception:
        close_reason = "error"
        raise
    finally:
        gauge_dec(websocket_connections_active)
        inc(websocket_disconnects_total, close_reason)
        try:
            await websocket.close()
        except Exception:
            pass
