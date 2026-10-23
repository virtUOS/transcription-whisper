import asyncio
import os
from app.config import settings


async def _write_without_metadata(input_path: str, output_path: str, codec_args: list[str]) -> str | None:
    """Write the audio of input_path to output_path without tags or cover art.

    Returns None on success, else the tail of ffmpeg's error output.
    """
    process = await asyncio.create_subprocess_exec(
        settings.FFMPEG_PATH, "-y", "-i", input_path,
        "-map_metadata", "-1", "-vn", *codec_args, output_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        # ffmpeg may have left a partial output behind
        if os.path.exists(output_path):
            os.unlink(output_path)
        return stderr.decode()[-500:] if stderr else "Unknown error"
    return None


async def convert_to_mp3(input_path: str) -> str:
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    # Always write a new file: the ASR host must not receive the upload's tags,
    # cover art or location. MP3 is stream-copied, everything else is re-encoded.
    stem = os.path.splitext(input_path)[0]
    if input_path.lower().endswith(".mp3"):
        output_path = stem + ".asr.mp3"
        # A file named .mp3 may hold other audio (AAC, WAV, ...), which the MP3
        # muxer rejects as is; re-encode it then.
        attempts = [["-c:a", "copy"], []]
    else:
        output_path = stem + ".mp3"
        attempts = [[]]

    for codec_args in attempts:
        error_msg = await _write_without_metadata(input_path, output_path, codec_args)
        if error_msg is None:
            return output_path
    raise RuntimeError(f"Audio conversion failed: {error_msg}")


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
