import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from fastapi.responses import FileResponse
from app.config import settings
from app.dependencies import get_current_user
from app.models import UserInfo, FileInfo
from app.database import get_db
from app.services.audio import convert_to_mp3

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".mp4"}
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB


@router.post("/api/upload", response_model=FileInfo)
async def upload_file(
    file: UploadFile,
    user: UserInfo = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.TEMP_PATH, f"{file_id}{ext}")

    os.makedirs(settings.TEMP_PATH, exist_ok=True)

    # Read file in chunks to avoid loading huge files into memory
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)  # 1MB chunks
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 1GB)")
        chunks.append(chunk)
    content = b"".join(chunks)
    file_size = total_size

    with open(file_path, "wb") as f:
        f.write(content)

    # Convert to MP3 if needed
    mp3_path = await convert_to_mp3(file_path)

    media_type = ext.lstrip(".")

    async with get_db() as db:
        # Ensure user exists
        await db.execute(
            "INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)",
            (user.id, user.email),
        )
        await db.execute(
            "INSERT INTO files (id, user_id, original_filename, file_path, mp3_path, media_type, file_size) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (file_id, user.id, file.filename, file_path, mp3_path, media_type, file_size),
        )
        await db.commit()

    return FileInfo(
        id=file_id,
        original_filename=file.filename or "",
        media_type=media_type,
        file_size=file_size,
    )


@router.get("/api/media/{file_id}")
async def get_media(
    file_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT file_path, media_type FROM files WHERE id = ? AND user_id = ?",
            (file_id, user.id),
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = row["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_types = {"mp3": "audio/mpeg", "wav": "audio/wav", "mp4": "video/mp4"}
    return FileResponse(file_path, media_type=media_types.get(row["media_type"], "application/octet-stream"))
