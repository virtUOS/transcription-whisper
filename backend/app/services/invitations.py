import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from aiosqlite import Connection

from app.config import settings


class DuplicatePendingInvitationError(Exception):
    """Raised when a pending invitation already exists for this email."""


class InvitationNotFoundError(Exception):
    """Raised when no invitation matches the given token or id."""


class InvitationExpiredError(Exception):
    """Raised when the invitation has passed its expires_at."""


class InvitationRevokedError(Exception):
    """Raised when the invitation was revoked."""


class InvitationAlreadyAcceptedError(Exception):
    """Raised when the invitation has already been accepted."""


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def create_invitation(
    db: Connection, *, email: str, created_by: str,
) -> dict:
    """Create a new invitation.

    Raises DuplicatePendingInvitationError if a pending, non-expired invitation
    for this email already exists.
    Returns dict with: id, email, token (raw), status, created_at, expires_at,
    created_by, accepted_at (None).
    """
    email_norm = _normalize_email(email)
    now_dt = datetime.now(timezone.utc)
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (now_dt + timedelta(days=settings.INVITATION_EXPIRY_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor = await db.execute(
        "SELECT id FROM invitations WHERE email = ? AND status = 'pending' AND expires_at > ?",
        (email_norm, now),
    )
    if await cursor.fetchone() is not None:
        raise DuplicatePendingInvitationError(
            f"A pending invitation already exists for {email_norm}"
        )

    raw_token = "tw_inv_" + secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    inv_id = str(uuid.uuid4())

    await db.execute(
        """
        INSERT INTO invitations
            (id, email, token_hash, created_by, created_at, expires_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
        (inv_id, email_norm, token_hash, created_by, now, expires_at),
    )
    await db.commit()

    return {
        "id": inv_id,
        "email": email_norm,
        "token": raw_token,
        "status": "pending",
        "created_at": now,
        "expires_at": expires_at,
        "created_by": created_by,
        "accepted_at": None,
    }
