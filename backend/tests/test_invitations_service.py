import asyncio
import pytest
from app.database import get_db
from app.services.invitations import (
    create_invitation,
    DuplicatePendingInvitationError,
    list_invitations,
    revoke_invitation,
    resolve_invitation_token,
    accept_invitation,
    expire_pending_invitations,
    cleanup_old_invitations,
    InvitationNotFoundError,
    InvitationExpiredError,
    InvitationRevokedError,
    InvitationAlreadyAcceptedError,
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


@pytest.mark.asyncio
async def test_list_returns_newest_first():
    async with get_db() as db:
        a = await create_invitation(db, email="a@example.com", created_by="admin@example.com")
        await asyncio.sleep(1.1)  # Ensure different timestamps (rounded to seconds)
        b = await create_invitation(db, email="b@example.com", created_by="admin@example.com")
        items = await list_invitations(db)
    assert [i["email"] for i in items][0:2] == ["b@example.com", "a@example.com"]


@pytest.mark.asyncio
async def test_revoke_sets_status_and_returns_true():
    async with get_db() as db:
        inv = await create_invitation(db, email="r@example.com", created_by="admin@example.com")
        ok = await revoke_invitation(db, invitation_id=inv["id"])
        assert ok is True
        cursor = await db.execute("SELECT status FROM invitations WHERE id = ?", (inv["id"],))
        row = await cursor.fetchone()
        assert row["status"] == "revoked"


@pytest.mark.asyncio
async def test_revoke_returns_false_for_unknown_id():
    async with get_db() as db:
        assert await revoke_invitation(db, invitation_id="does-not-exist") is False


@pytest.mark.asyncio
async def test_resolve_invitation_token_returns_row_when_pending():
    async with get_db() as db:
        inv = await create_invitation(db, email="res@example.com", created_by="admin@example.com")
        row = await resolve_invitation_token(db, raw_token=inv["token"])
    assert row is not None
    assert row["email"] == "res@example.com"
    assert row["status"] == "pending"


@pytest.mark.asyncio
async def test_resolve_invitation_token_raises_for_expired():
    from datetime import datetime, timezone, timedelta
    async with get_db() as db:
        inv = await create_invitation(db, email="e@example.com", created_by="admin@example.com")
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute("UPDATE invitations SET expires_at = ? WHERE id = ?", (past, inv["id"]))
        await db.commit()
        with pytest.raises(InvitationExpiredError):
            await resolve_invitation_token(db, raw_token=inv["token"])


@pytest.mark.asyncio
async def test_resolve_invitation_token_raises_for_revoked():
    async with get_db() as db:
        inv = await create_invitation(db, email="rv@example.com", created_by="admin@example.com")
        await revoke_invitation(db, invitation_id=inv["id"])
        with pytest.raises(InvitationRevokedError):
            await resolve_invitation_token(db, raw_token=inv["token"])


@pytest.mark.asyncio
async def test_resolve_unknown_token_raises_not_found():
    async with get_db() as db:
        with pytest.raises(InvitationNotFoundError):
            await resolve_invitation_token(db, raw_token="tw_inv_doesnotexist")


@pytest.mark.asyncio
async def test_accept_invitation_marks_accepted_and_blocks_reuse():
    async with get_db() as db:
        inv = await create_invitation(db, email="ac@example.com", created_by="admin@example.com")
        await accept_invitation(db, raw_token=inv["token"], user_id="kc-sub-123")
        with pytest.raises(InvitationAlreadyAcceptedError):
            await resolve_invitation_token(db, raw_token=inv["token"])


@pytest.mark.asyncio
async def test_expire_pending_invitations_transitions_stale_rows():
    from datetime import datetime, timezone, timedelta
    async with get_db() as db:
        inv = await create_invitation(db, email="ex@example.com", created_by="admin@example.com")
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute("UPDATE invitations SET expires_at = ? WHERE id = ?", (past, inv["id"]))
        await db.commit()
        changed = await expire_pending_invitations(db)
        assert changed == 1
        cursor = await db.execute("SELECT status FROM invitations WHERE id = ?", (inv["id"],))
        row = await cursor.fetchone()
        assert row["status"] == "expired"


@pytest.mark.asyncio
async def test_cleanup_old_invitations_deletes_30_day_terminal_rows():
    from datetime import datetime, timezone, timedelta
    async with get_db() as db:
        inv = await create_invitation(db, email="old@example.com", created_by="admin@example.com")
        await revoke_invitation(db, invitation_id=inv["id"])
        long_ago = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d %H:%M:%S")
        await db.execute("UPDATE invitations SET created_at = ? WHERE id = ?", (long_ago, inv["id"]))
        await db.commit()
        deleted = await cleanup_old_invitations(db)
        assert deleted == 1
        cursor = await db.execute("SELECT id FROM invitations WHERE id = ?", (inv["id"],))
        assert await cursor.fetchone() is None


@pytest.mark.asyncio
async def test_accept_invitation_loses_race_to_revoke():
    async with get_db() as db:
        inv = await create_invitation(
            db, email="race@example.com", created_by="admin@example.com",
        )
        # Simulate the row being revoked between resolve and update
        await db.execute(
            "UPDATE invitations SET status = 'revoked' WHERE id = ?", (inv["id"],)
        )
        await db.commit()
        with pytest.raises(InvitationRevokedError):
            await accept_invitation(db, raw_token=inv["token"], user_id="kc-sub-race")
        # Confirm the status was NOT clobbered to 'accepted'
        cursor = await db.execute(
            "SELECT status FROM invitations WHERE id = ?", (inv["id"],)
        )
        row = await cursor.fetchone()
        assert row["status"] == "revoked"
