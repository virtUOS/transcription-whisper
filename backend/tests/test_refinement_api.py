import pytest
from app.database import get_db


@pytest.mark.asyncio
async def test_refinement_columns_exist():
    """Verify the transcriptions table has refinement columns."""
    async with get_db() as db:
        cursor = await db.execute("PRAGMA table_info(transcriptions)")
        columns = {row[1] for row in await cursor.fetchall()}
    assert "refined_utterances_json" in columns
    assert "refinement_metadata_json" in columns
