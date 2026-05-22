import pytest
from datetime import datetime, timedelta, timezone

from prometheus_client import REGISTRY

from app.database import get_db


def _fmt(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _g(name: str, **labels) -> float:
    """Read a gauge's current sample value from the default registry."""
    val = REGISTRY.get_sample_value(name, labels or None)
    assert val is not None, f"metric {name}{labels} not registered (is ENABLE_METRICS set?)"
    return val


@pytest.mark.asyncio
async def test_refresh_user_gauges_counts_users_and_recent_cohorts():
    # Arrange: insert 5 users with first_seen spread across recency buckets,
    # and 4 transcription rows (3 distinct users + 1 NULL user_id).
    now = datetime.now(timezone.utc)
    fixtures = [
        ("u_today",  "today@example.com",      _fmt(now)),
        ("u_5d",     "fivedays@example.com",   _fmt(now - timedelta(days=5))),
        ("u_20d",    "twentydays@example.com", _fmt(now - timedelta(days=20))),
        ("u_100d",   "old1@example.com",       _fmt(now - timedelta(days=100))),
        ("u_lurker", "lurker@example.com",     _fmt(now - timedelta(days=2))),
    ]
    async with get_db() as db:
        for uid, email, first_seen in fixtures:
            await db.execute(
                "INSERT INTO users (id, email, first_seen, last_active) VALUES (?, ?, ?, ?)",
                (uid, email, first_seen, first_seen),
            )
        # 3 transcriptions owned by 3 distinct users; 1 transcription with NULL user_id.
        await db.execute(
            "INSERT INTO transcriptions (id, user_id, status) VALUES (?, ?, ?)",
            ("t1", "u_today", "completed"),
        )
        await db.execute(
            "INSERT INTO transcriptions (id, user_id, status) VALUES (?, ?, ?)",
            ("t2", "u_5d", "completed"),
        )
        await db.execute(
            "INSERT INTO transcriptions (id, user_id, status) VALUES (?, ?, ?)",
            ("t3", "u_100d", "completed"),
        )
        await db.execute(
            "INSERT INTO transcriptions (id, user_id, status) VALUES (?, ?, ?)",
            ("t4", None, "completed"),
        )
        await db.commit()

    # Act
    from app.main import refresh_user_gauges
    async with get_db() as db:
        await refresh_user_gauges(db)

    # Assert
    assert _g("transcription_users_total") == 5
    assert _g("transcription_users_with_transcriptions") == 3   # NULL user_id excluded
    assert _g("transcription_users_new", window="7d") == 3      # today, 5d, lurker(2d)
    assert _g("transcription_users_new", window="30d") == 4     # plus 20d


@pytest.mark.asyncio
async def test_refresh_user_gauges_on_empty_db_yields_zero():
    from app.main import refresh_user_gauges
    async with get_db() as db:
        await refresh_user_gauges(db)
    assert _g("transcription_users_total") == 0
    assert _g("transcription_users_with_transcriptions") == 0
    assert _g("transcription_users_new", window="7d") == 0
    assert _g("transcription_users_new", window="30d") == 0