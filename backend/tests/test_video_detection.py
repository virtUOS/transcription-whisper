import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_has_video_stream_returns_true_for_video():
    from app.services.audio import has_video_stream

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"video\n", b"")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await has_video_stream("/fake/file.mp4")
    assert result is True


@pytest.mark.asyncio
async def test_has_video_stream_returns_false_for_audio_only():
    from app.services.audio import has_video_stream

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await has_video_stream("/fake/file.webm")
    assert result is False


@pytest.mark.asyncio
async def test_has_video_stream_returns_false_on_ffprobe_error():
    from app.services.audio import has_video_stream

    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        result = await has_video_stream("/fake/file.webm")
    assert result is False
