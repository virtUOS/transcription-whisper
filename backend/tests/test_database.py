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


@pytest.mark.asyncio
async def test_api_tokens_table_created(tmp_path):
    db_path = str(tmp_path / "api_tokens.db")
    await init_db(db_path)
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_tokens'"
        )
        row = await cursor.fetchone()
    assert row is not None


@pytest.mark.asyncio
async def test_api_tokens_hash_index_created(tmp_path):
    db_path = str(tmp_path / "api_tokens_idx.db")
    await init_db(db_path)
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_api_tokens_hash'"
        )
        row = await cursor.fetchone()
    assert row is not None


@pytest.mark.asyncio
async def test_source_tracking_columns_exist(tmp_path):
    db_path = str(tmp_path / "source_tracking.db")
    await init_db(db_path)
    async with get_db(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(transcriptions)")
        txn_columns = {row[1] for row in await cursor.fetchall()}
        cursor = await db.execute("PRAGMA table_info(analyses)")
        ana_columns = {row[1] for row in await cursor.fetchall()}
    assert "translation_source" in txn_columns
    assert "translation_source_hash" in txn_columns
    assert "source" in ana_columns
    assert "source_hash" in ana_columns
