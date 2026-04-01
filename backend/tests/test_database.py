import pytest
from app.database import init_db, get_db


@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_db_path):
    await init_db(tmp_db_path)
    async with get_db(tmp_db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]
    assert "users" in tables
    assert "files" in tables
    assert "transcriptions" in tables
    assert "speaker_mappings" in tables
    assert "analyses" in tables


@pytest.mark.asyncio
async def test_init_db_is_idempotent(tmp_db_path):
    await init_db(tmp_db_path)
    await init_db(tmp_db_path)  # Should not raise


@pytest.mark.asyncio
async def test_has_video_column_exists(tmp_path):
    db_path = str(tmp_path / "migration_test.db")
    await init_db(db_path)
    async with get_db(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(files)")
        columns = {row[1] for row in await cursor.fetchall()}
    assert "has_video" in columns
