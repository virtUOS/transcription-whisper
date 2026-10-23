import asyncio
import logging
import httpx
from app.config import settings
from app.metrics import inc, errors_total
from app.services.asr.base import ASRBackend, TranscriptionSettings
from app.models import TranscriptionStatus, TranscriptionResult, Utterance

STATUS_MAP = {
    "queued": "pending",
    "processing": "processing",
    "completed": "completed",
    "error": "failed",
    "failed": "failed",
}

# Seconds to wait before each retry of a remote delete (3 attempts in all).
CLEANUP_RETRY_DELAYS = (1, 2)

class MurmurAIBackend(ASRBackend):
    def __init__(self):
        self.base_url = settings.ASR_URL
        self.headers = {"Authorization": settings.ASR_API_KEY}

    async def submit(self, file_path: str, ts: TranscriptionSettings) -> str:
        enable_diarization = ts.min_speakers > 0 or ts.max_speakers > 0
        data = {
            "speaker_labels": str(enable_diarization).lower(),
            "word_timestamps": "true",
        }
        if ts.language and ts.language != "auto":
            data["language_code"] = ts.language
        if ts.model:
            data["model"] = ts.model
        if enable_diarization:
            if ts.min_speakers > 0:
                data["min_speakers"] = str(ts.min_speakers)
            if ts.max_speakers > 0:
                data["max_speakers"] = str(ts.max_speakers)
        if ts.initial_prompt:
            data["initial_prompt"] = ts.initial_prompt
        if ts.hotwords:
            data["hotwords"] = ts.hotwords

        async with httpx.AsyncClient(timeout=300) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{self.base_url}/v1/transcript",
                    headers=self.headers,
                    files={"file": f},
                    data=data,
                )
            response.raise_for_status()
            return response.json()["id"]

    async def get_status(self, job_id: str) -> TranscriptionStatus:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/v1/transcript/{job_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()

        raw_status = str(result.get("status", "")).lower()
        mapped = STATUS_MAP.get(raw_status, raw_status)
        return TranscriptionStatus(id=job_id, status=mapped, error=result.get("error"))

    async def get_result(self, job_id: str) -> TranscriptionResult:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/v1/transcript/{job_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()

        utterances = [
            Utterance(start=utt.get("start", 0), end=utt.get("end", 0),
                      text=utt.get("text", ""), speaker=utt.get("speaker"))
            for utt in result.get("utterances", [])
        ]
        full_text = result.get("text", " ".join(u.text for u in utterances))
        return TranscriptionResult(id=job_id, status="completed", utterances=utterances,
                                   text=full_text, language=result.get("language"))

    async def cleanup(self, job_id: str) -> None:
        """Delete the transcript from the MurmurAI server.

        MurmurAI keeps every transcript until a client deletes it. The app holds
        its own copy, so the remote one goes as soon as it has been read. Retried
        a few times, since a restart can leave the server briefly unreachable; a
        404 means it is already gone. Best effort: a failure is logged and
        counted, never raised.
        """
        for delay in (*CLEANUP_RETRY_DELAYS, None):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.delete(
                        f"{self.base_url}/v1/transcript/{job_id}",
                        headers=self.headers,
                    )
                    if response.status_code == 404:
                        return
                    response.raise_for_status()
                return
            except Exception as e:
                if delay is not None:
                    await asyncio.sleep(delay)
                    continue
                logging.warning("Could not delete remote transcript %s from MurmurAI: %s", job_id, e)
                inc(errors_total, "asr_cleanup_failed", "asr")
                print(f"Cleanup error: {e}")
