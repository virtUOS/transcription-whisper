import os
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from fastapi.responses import FileResponse
from app.config import settings
from app.dependencies import get_current_user
from app.router_helpers import fetch_file_owned_or_404
from app.models import UserInfo, FileInfo, RenameRequest
from app.database import get_db
from app.services.audio import convert_to_mp3, has_video_stream
from app.metrics import inc, observe, file_uploads_total, file_upload_size_bytes, file_renames_total, errors_total

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".mp4", ".webm", ".m4a", ".mov", ".aac", ".opus", ".ogg"}
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB


@router.post("/api/upload", response_model=FileInfo)
async def upload_file(
    file: UploadFile,
    has_video: bool | None = None,
    user: UserInfo = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        inc(file_uploads_total, ext.lstrip("."), "rejected")
        inc(errors_total, "unsupported_file_type", "upload")
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.TEMP_PATH, f"{file_id}{ext}")

    os.makedirs(settings.TEMP_PATH, exist_ok=True)

    # Stream file to disk in chunks, reject early if too large
    total_size = 0
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    inc(file_uploads_total, ext.lstrip("."), "rejected")
                    inc(errors_total, "file_too_large", "upload")
                    raise HTTPException(status_code=413, detail="File too large (max 1GB)")
                f.write(chunk)
    except HTTPException:
        # Clean up partial file on rejection
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    file_size = total_size

    # Convert to MP3 if needed
    mp3_path = await convert_to_mp3(file_path)

    # Detect video tracks
    if has_video is None:
        # Pure audio extensions never have video
        audio_only_exts = {".mp3", ".wav", ".m4a", ".aac", ".opus", ".ogg"}
        if ext in audio_only_exts:
            has_video = False
        else:
            has_video = await has_video_stream(file_path)

    media_type = ext.lstrip(".")
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=settings.DEFAULT_EXPIRY_HOURS)).strftime("%Y-%m-%d %H:%M:%S")

    async with get_db() as db:
        # Ensure user exists
        await db.execute(
            "INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)",
            (user.id, user.email),
        )
        await db.execute(
            "INSERT INTO files (id, user_id, original_filename, file_path, mp3_path, media_type, file_size, expires_at, has_video) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (file_id, user.id, file.filename, file_path, mp3_path, media_type, file_size, expires_at, int(has_video)),
        )
        await db.commit()

    inc(file_uploads_total, media_type, "success")
    observe(file_upload_size_bytes, file_size)

    return FileInfo(
        id=file_id,
        original_filename=file.filename or "",
        media_type=media_type,
        file_size=file_size,
        has_video=has_video,
    )


@router.get("/api/media/{file_id}")
async def get_media(
    file_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        row = await fetch_file_owned_or_404(db, file_id, user.id)

    file_path = row["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_types = {"mp3": "audio/mpeg", "wav": "audio/wav", "mp4": "video/mp4", "webm": "video/webm", "m4a": "audio/mp4", "mov": "video/quicktime", "aac": "audio/aac", "opus": "audio/opus", "ogg": "audio/ogg"}
    return FileResponse(file_path, media_type=media_types.get(row["media_type"], "application/octet-stream"))


@router.get("/api/media/{file_id}/fallback")
async def get_media_fallback(
    file_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        row = await fetch_file_owned_or_404(db, file_id, user.id, detail="No fallback available")

    if not row["mp3_path"]:
        raise HTTPException(status_code=404, detail="No fallback available")

    mp3_path = row["mp3_path"]
    if not os.path.exists(mp3_path):
        raise HTTPException(status_code=404, detail="Fallback file not found on disk")

    return FileResponse(mp3_path, media_type="audio/mpeg")


@router.patch("/api/files/{file_id}/rename", response_model=FileInfo)
async def rename_file(
    file_id: str,
    body: RenameRequest,
    user: UserInfo = Depends(get_current_user),
):
    filename = body.filename.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    async with get_db() as db:
        row = await fetch_file_owned_or_404(db, file_id, user.id)

        # Preserve original extension
        original_ext = os.path.splitext(row["original_filename"])[1]
        new_filename = filename + original_ext

        if len(new_filename) > 255:
            raise HTTPException(status_code=400, detail="Filename too long")

        await db.execute(
            "UPDATE files SET original_filename = ? WHERE id = ? AND user_id = ?",
            (new_filename, file_id, user.id),
        )
        await db.commit()

    inc(file_renames_total)

    return FileInfo(
        id=file_id,
        original_filename=new_filename,
        media_type=row["media_type"],
        file_size=row["file_size"],
        has_video=bool(row["has_video"]),
    )
