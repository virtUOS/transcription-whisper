import asyncio
import os
from app.config import settings


async def convert_to_mp3(input_path: str) -> str:
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    if input_path.lower().endswith(".mp3"):
        return input_path

    output_path = os.path.splitext(input_path)[0] + ".mp3"

    process = await asyncio.create_subprocess_exec(
        settings.FFMPEG_PATH, "-y", "-i", input_path, output_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode()[-500:] if stderr else "Unknown error"
        raise RuntimeError(f"Audio conversion failed: {error_msg}")

    return output_path


async def get_media_duration(file_path: str) -> float | None:
    """Return the duration of a media file in seconds, or None on failure."""
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            settings.FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        return float(stdout.decode().strip())
    except (FileNotFoundError, OSError, ValueError):
        return None
    except asyncio.CancelledError:
        if process and process.returncode is None:
            process.kill()
            try:
                await process.wait()
            except Exception:
                pass
        raise


async def has_video_stream(file_path: str) -> bool:
    """Check if a media file contains a video stream using ffprobe."""
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            settings.FFPROBE_PATH, "-v", "error", "-select_streams", "v",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0", file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        return b"video" in stdout
    except (FileNotFoundError, OSError):
        return False
    except asyncio.CancelledError:
        if process and process.returncode is None:
            process.kill()
            try:
                await process.wait()
            except Exception:
                pass
        raise
