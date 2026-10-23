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


@pytest.mark.asyncio
async def test_failed_conversion_removes_partial_output(tmp_path, monkeypatch):
    from app.services.audio import settings
    fake_ffmpeg = tmp_path / "ffmpeg"
    # Like ffmpeg, writes the output file (last argument) before failing.
    fake_ffmpeg.write_text('#!/bin/sh\nfor a; do last="$a"; done\necho partial > "$last"\nexit 1\n')
    fake_ffmpeg.chmod(0o755)
    monkeypatch.setattr(settings, "FFMPEG_PATH", str(fake_ffmpeg))
    work = tmp_path / "work"
    work.mkdir()
    src = work / "in.wav"
    src.write_bytes(b"not audio")

    with pytest.raises(RuntimeError):
        await convert_to_mp3(str(src))

    assert os.listdir(work) == ["in.wav"]
