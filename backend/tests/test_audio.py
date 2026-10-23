import os
import shutil
import subprocess
import pytest
from app.services.audio import convert_to_mp3


def _ffmpeg(*args):
    from app.services.audio import settings
    if shutil.which(settings.FFMPEG_PATH) is None:
        pytest.skip("ffmpeg not installed")
    subprocess.run([settings.FFMPEG_PATH, "-y", "-loglevel", "error", *args], check=True)


def _probe(path):
    from app.services.audio import settings
    return subprocess.run(
        [settings.FFPROBE_PATH, "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout


@pytest.mark.asyncio
async def test_mp3_tags_and_cover_stripped(tmp_path):
    cover = tmp_path / "cover.png"
    _ffmpeg("-f", "lavfi", "-i", "color=c=red:s=16x16", "-frames:v", "1", str(cover))
    src = tmp_path / "in.mp3"
    _ffmpeg(
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-i", str(cover),
        "-map", "0:a", "-map", "1:v", "-c:a", "libmp3lame", "-c:v", "copy",
        "-id3v2_version", "3", "-metadata", "title=SECRET-TITLE",
        "-metadata:s:v", "title=Album cover", str(src),
    )
    original = src.read_bytes()
    assert "SECRET-TITLE" in _probe(src)

    result = await convert_to_mp3(str(src))

    assert result != str(src)
    assert result.endswith(".asr.mp3")
    probe = _probe(result)
    assert "SECRET-TITLE" not in probe
    assert "codec_type=video" not in probe
    assert src.read_bytes() == original


@pytest.mark.asyncio
async def test_mp4_metadata_stripped(tmp_path):
    src = tmp_path / "in.mp4"
    _ffmpeg(
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-metadata", "title=SECRET-TITLE", "-metadata", "location=+52.27+008.04/",
        str(src),
    )
    probe = _probe(src)
    assert "SECRET-TITLE" in probe and "+52.2700+008.0400" in probe

    result = await convert_to_mp3(str(src))

    assert result == str(tmp_path / "in.mp3")
    probe = _probe(result)
    assert "SECRET-TITLE" not in probe
    assert "+52.2700+008.0400" not in probe


@pytest.mark.asyncio
async def test_convert_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        await convert_to_mp3("/nonexistent/file.wav")


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["in.wav", "in.mp3"])
async def test_failed_conversion_removes_partial_output(tmp_path, monkeypatch, name):
    from app.services.audio import settings
    fake_ffmpeg = tmp_path / "ffmpeg"
    # Like ffmpeg, writes the output file (last argument) before failing.
    fake_ffmpeg.write_text('#!/bin/sh\nfor a; do last="$a"; done\necho partial > "$last"\nexit 1\n')
    fake_ffmpeg.chmod(0o755)
    monkeypatch.setattr(settings, "FFMPEG_PATH", str(fake_ffmpeg))
    work = tmp_path / "work"
    work.mkdir()
    src = work / name
    src.write_bytes(b"not audio")

    with pytest.raises(RuntimeError):
        await convert_to_mp3(str(src))

    assert os.listdir(work) == [name]
