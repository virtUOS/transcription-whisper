import pytest
from app.database import get_db


@pytest.mark.asyncio
async def test_invitations_table_exists():
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='invitations'"
        )
        row = await cursor.fetchone()
        assert row is not None


@pytest.mark.asyncio
async def test_invitations_table_columns():
    async with get_db() as db:
        cursor = await db.execute("PRAGMA table_info(invitations)")
        cols = {row["name"] for row in await cursor.fetchall()}
    expected = {
        "id", "email", "token_hash", "created_by", "created_at",
        "expires_at", "status", "accepted_at", "accepted_by_user_id",
    }
    assert expected.issubset(cols)


@pytest.mark.asyncio
async def test_invitations_email_and_status_indexes_exist():
    async with get_db() as db:
        cursor = await db.execute("PRAGMA index_list(invitations)")
        idx_names = {row["name"] for row in await cursor.fetchall()}
    assert "idx_invitations_email" in idx_names
    assert "idx_invitations_status" in idx_names
