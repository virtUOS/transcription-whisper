import os
import tempfile
import pytest
from app.services.audio import convert_to_mp3


@pytest.mark.asyncio
async def test_convert_mp3_returns_same_path():
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"fake mp3 data")
        path = f.name
    try:
        result = await convert_to_mp3(path)
        assert result == path
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_convert_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        await convert_to_mp3("/nonexistent/file.wav")
