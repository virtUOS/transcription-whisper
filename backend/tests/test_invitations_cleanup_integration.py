import pytest
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.services.invitations import (
    create_invitation, expire_pending_invitations, cleanup_old_invitations,
)


@pytest.mark.asyncio
async def test_cleanup_functions_are_idempotent_and_return_counts():
    # First call: nothing to do
    async with get_db() as db:
        assert await expire_pending_invitations(db) == 0
        assert await cleanup_old_invitations(db) == 0

    # Create a pending invitation, artificially age it past expiry
    async with get_db() as db:
        inv = await create_invitation(
            db, email="aged@example.com", created_by="admin@example.com",
        )
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            "UPDATE invitations SET expires_at = ? WHERE id = ?",
            (past, inv["id"]),
        )
        await db.commit()

    # expire transitions pending→expired
    async with get_db() as db:
        assert await expire_pending_invitations(db) == 1

    # Second call: nothing left to expire
    async with get_db() as db:
        assert await expire_pending_invitations(db) == 0
