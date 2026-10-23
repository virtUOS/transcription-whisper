import os
os.environ.setdefault("ENABLE_API_TOKENS", "true")
os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("ENABLE_METRICS", "true")

import asyncio
import tempfile
import pytest
import pytest_asyncio
from app.database import init_db


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


@pytest.fixture(autouse=True)
def fake_convert_to_mp3(monkeypatch):
    """Uploads in these tests carry placeholder bytes, which ffmpeg would reject.
    Mimics the real contract: always a new file next to the original."""
    import shutil

    async def _convert(input_path):
        stem, ext = os.path.splitext(input_path)
        output_path = stem + (".asr.mp3" if ext.lower() == ".mp3" else ".mp3")
        shutil.copyfile(input_path, output_path)
        return output_path

    monkeypatch.setattr("app.routers.upload.convert_to_mp3", _convert)
