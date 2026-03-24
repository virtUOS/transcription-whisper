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
