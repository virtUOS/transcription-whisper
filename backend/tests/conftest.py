import os
os.environ.setdefault("ENABLE_API_TOKENS", "true")
os.environ.setdefault("DEV_MODE", "true")

import asyncio
import tempfile
import pytest
import pytest_asyncio
from app.database import init_db, get_db


@pytest.fixture
def tmp_db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test.db")


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def init_test_db(tmp_path):
    """Initialize a fresh DB for each async test."""
    db_path = str(tmp_path / "test.db")
    await init_db(db_path)
