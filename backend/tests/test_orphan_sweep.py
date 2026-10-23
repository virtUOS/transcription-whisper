"""Media files in TEMP_PATH that no DB row references are swept after 24 h."""
import os
import time
import uuid

import pytest

from app.database import get_db
from app.main import ORPHAN_MIN_AGE_HOURS, delete_orphaned_media


def _touch(directory, name, age_hours):
    path = os.path.join(directory, name)
    with open(path, "wb") as f:
        f.write(b"x")
    mtime = time.time() - age_hours * 3600
    os.utime(path, (mtime, mtime))
    return path


@pytest.mark.asyncio
async def test_orphan_sweep(tmp_path):
    old = ORPHAN_MIN_AGE_HOURS + 1
    orphan = _touch(tmp_path, f"{uuid.uuid4()}.wav", old)
    referenced = _touch(tmp_path, f"{uuid.uuid4()}.mp3", old)
    fresh = _touch(tmp_path, f"{uuid.uuid4()}.mp4", 1)
    db_file = _touch(tmp_path, "transcription.db", old)
    notes = _touch(tmp_path, "notes.txt", old)

    async with get_db() as db:
        await db.execute("INSERT INTO users (id, email) VALUES ('u', 'u@x')")
        await db.execute(
            "INSERT INTO files (id, user_id, original_filename, file_path, mp3_path, media_type, file_size, expires_at) "
            "VALUES ('f', 'u', 'a.mp3', ?, ?, 'mp3', 1, '2999-01-01 00:00:00')",
            (referenced, referenced),
        )
        await db.commit()

    # Passed explicitly: tests elsewhere reload app.config, so patching a settings
    # object here could leave the sweep reading the real TEMP_PATH.
    assert await delete_orphaned_media(temp_path=str(tmp_path)) == 1

    assert not os.path.exists(orphan)
    for kept in (referenced, fresh, db_file, notes):
        assert os.path.exists(kept)
