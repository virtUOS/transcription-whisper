import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config import settings
from app.database import get_db
from app.metrics import (
    inc, gauge_inc, gauge_dec,
    websocket_connections_active, websocket_connections_total,
    transcriptions_total, errors_total,
)

router = APIRouter()

# Limit concurrent live sessions
_live_semaphore = asyncio.Semaphore(int(settings.ASR_MAX_CONCURRENT))


def parse_wlk_timestamp(ts: str) -> int:
    """Parse WLK 'H:MM:SS' or 'H:MM:SS.mmm' timestamp to milliseconds."""
    parts = ts.split(":")
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    return int((h * 3600 + m * 60 + s) * 1000)


def wlk_lines_to_utterances(lines: list[dict]) -> list[dict]:
    """Convert WLK line objects to Utterance dicts."""
    utterances = []
    for line in lines:
        raw_speaker = line.get("speaker")
        if raw_speaker is not None and raw_speaker != -2:
            speaker = f"Speaker {raw_speaker}"
        else:
            speaker = None
        text = line.get("text")
        if not text:
            continue
        utterances.append({
            "start": parse_wlk_timestamp(line.get("start", "0:00:00")),
            "end": parse_wlk_timestamp(line.get("end", "0:00:00")),
            "text": text.strip(),
            "speaker": speaker,
        })
    return utterances


@router.websocket("/api/ws/live")
async def websocket_live(websocket: WebSocket):
    if not settings.LIVE_TRANSCRIPTION_ENABLED or not settings.WLK_WS_URL:
        await websocket.close(code=4003, reason="Live transcription not available")
        return

    await websocket.accept()
    inc(websocket_connections_total)
    gauge_inc(websocket_connections_active)

    user_id = websocket.headers.get("x-forwarded-user", "anonymous")
    language = websocket.query_params.get("language", "")

    transcription_id = str(uuid.uuid4())
    file_id = str(uuid.uuid4())
    accumulated_lines: list[dict] = []
    wlk_ws = None

    try:
        # Create DB records for the live session
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=settings.DEFAULT_EXPIRY_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        filename = f"live-session-{now.strftime('%Y%m%d-%H%M%S')}.pcm"

        async with get_db() as db:
            await db.execute(
                """INSERT INTO files (id, user_id, original_filename, file_path, mp3_path,
                   media_type, file_size, created_at, expires_at, is_archived)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_id, user_id, filename, "", "", "audio/pcm", 0,
                 now.strftime("%Y-%m-%d %H:%M:%S"), expires_at, 0),
            )
            await db.execute(
                """INSERT INTO transcriptions
                   (id, user_id, file_id, asr_backend, status, language, model,
                    min_speakers, max_speakers, initial_prompt, hotwords, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (transcription_id, user_id, file_id, "whisperlivekit_live", "live",
                 language or None, None, 0, 0, None, None,
                 now.strftime("%Y-%m-%d %H:%M:%S")),
            )
            await db.commit()

        # Notify browser of the session ID
        await websocket.send_json({
            "type": "session_started",
            "transcription_id": transcription_id,
        })

        # Connect to WhisperLiveKit
        wlk_url = f"{settings.WLK_WS_URL}/asr"
        params = []
        if language:
            params.append(f"language={language}")
        params.append("mode=full")
        if params:
            wlk_url += "?" + "&".join(params)

        async with _live_semaphore:
            async with websockets.connect(wlk_url) as wlk_ws:
                # Read and forward WLK config message
                config_msg = await wlk_ws.recv()
                config_data = json.loads(config_msg)
                await websocket.send_json({
                    "type": "config",
                    "pcm_required": config_data.get("useAudioWorklet", False),
                })

                async def forward_browser_to_wlk():
                    """Forward audio frames from browser to WLK."""
                    try:
                        while True:
                            data = await websocket.receive_bytes()
                            await wlk_ws.send(data)
                            if len(data) == 0:
                                # Empty frame = end of audio
                                break
                    except WebSocketDisconnect:
                        # Browser disconnected, signal end to WLK
                        await wlk_ws.send(b"")

                async def forward_wlk_to_browser():
                    """Forward transcription results from WLK to browser."""
                    nonlocal accumulated_lines
                    try:
                        async for message in wlk_ws:
                            msg_data = json.loads(message)

                            if msg_data.get("type") == "ready_to_stop":
                                break

                            # Extract lines and buffer
                            lines = msg_data.get("lines", [])
                            buffer_text = msg_data.get("buffer_transcription", "")

                            # Accumulate latest full state of lines
                            if lines:
                                accumulated_lines = lines

                            # Forward to browser in our format
                            utterances = wlk_lines_to_utterances(lines)
                            await websocket.send_json({
                                "type": "transcription_update",
                                "lines": utterances,
                                "buffer_text": buffer_text,
                            })
                    except websockets.exceptions.ConnectionClosed:
                        pass

                # Run both directions concurrently
                browser_task = asyncio.create_task(forward_browser_to_wlk())
                wlk_task = asyncio.create_task(forward_wlk_to_browser())

                done, pending = await asyncio.wait(
                    [browser_task, wlk_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass

        # Save final result to DB
        final_utterances = wlk_lines_to_utterances(accumulated_lines)
        async with get_db() as db:
            await db.execute(
                """UPDATE transcriptions SET status = ?, result_json = ?, completed_at = ?
                   WHERE id = ?""",
                ("completed", json.dumps(final_utterances),
                 datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                 transcription_id),
            )
            await db.commit()

        inc(transcriptions_total, language or "auto", "live", "completed")

        # Notify browser
        await websocket.send_json({
            "type": "session_complete",
            "transcription_id": transcription_id,
        })

    except WebSocketDisconnect:
        # Browser left — save whatever we have
        if accumulated_lines:
            final_utterances = wlk_lines_to_utterances(accumulated_lines)
            async with get_db() as db:
                await db.execute(
                    """UPDATE transcriptions SET status = ?, result_json = ?, completed_at = ?
                       WHERE id = ?""",
                    ("completed", json.dumps(final_utterances),
                     datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                     transcription_id),
                )
                await db.commit()
        else:
            async with get_db() as db:
                await db.execute(
                    "UPDATE transcriptions SET status = ?, error_message = ? WHERE id = ?",
                    ("failed", "Session disconnected with no results", transcription_id),
                )
                await db.commit()

    except Exception as e:
        inc(errors_total, "live_transcription_failed", "asr")
        inc(transcriptions_total, language or "auto", "live", "failed")

        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET status = ?, error_message = ? WHERE id = ?",
                ("failed", str(e), transcription_id),
            )
            await db.commit()

        try:
            await websocket.send_json({"type": "error", "detail": str(e)})
        except Exception:
            pass

    finally:
        gauge_dec(websocket_connections_active)
        try:
            await websocket.close()
        except Exception:
            pass
