import pytest
from app.database import get_db
from app.services.invitations import (
    create_invitation,
    DuplicatePendingInvitationError,
)


@pytest.mark.asyncio
async def test_create_invitation_returns_raw_token_and_hashes_it():
    async with get_db() as db:
        result = await create_invitation(
            db, email="new@example.com", created_by="admin@example.com",
        )
    assert result["token"].startswith("tw_inv_")
    assert result["email"] == "new@example.com"
    assert result["status"] == "pending"
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT token_hash FROM invitations WHERE id = ?", (result["id"],)
        )
        row = await cursor.fetchone()
    assert row is not None
    assert row["token_hash"] != result["token"]


@pytest.mark.asyncio
async def test_create_invitation_normalizes_email_lowercase():
    async with get_db() as db:
        result = await create_invitation(
            db, email="Mixed@EXAMPLE.com", created_by="admin@example.com",
        )
    assert result["email"] == "mixed@example.com"


@pytest.mark.asyncio
async def test_create_invitation_rejects_duplicate_pending():
    async with get_db() as db:
        await create_invitation(db, email="x@example.com", created_by="admin@example.com")
        with pytest.raises(DuplicatePendingInvitationError):
            await create_invitation(db, email="x@example.com", created_by="admin@example.com")
