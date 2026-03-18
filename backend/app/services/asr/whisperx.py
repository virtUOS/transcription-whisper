import asyncio
import uuid
import httpx
from app.config import settings
from app.services.asr.base import ASRBackend, TranscriptionSettings
from app.models import TranscriptionStatus, TranscriptionResult, Utterance

_semaphore = asyncio.Semaphore(settings.ASR_MAX_CONCURRENT)

# In-memory cache for WhisperX results. WhisperX is synchronous, so submit() blocks
# until complete — the result is stored in the DB by _run_transcription() immediately
# after submit() returns. These dicts are only used during the brief poll loop between
# submit() returning and _run_transcription() reading get_result().
_results: dict[str, TranscriptionResult] = {}
_statuses: dict[str, str] = {}


class WhisperXBackend(ASRBackend):
    def __init__(self):
        self.base_url = settings.ASR_URL

    async def submit(self, file_path: str, ts: TranscriptionSettings) -> str:
        job_id = str(uuid.uuid4())
        _statuses[job_id] = "processing"

        async with _semaphore:
            try:
                result = await self._call_whisperx(file_path, ts)
                _results[job_id] = result
                _statuses[job_id] = "completed"
            except Exception as e:
                _statuses[job_id] = "failed"
                _results[job_id] = TranscriptionResult(
                    id=job_id, status="failed", text="", utterances=[], language=None
                )
                raise

        return job_id

    async def _call_whisperx(self, file_path: str, ts: TranscriptionSettings) -> TranscriptionResult:
        data = {
            "response_format": "verbose_json",
            "diarize": str(ts.min_speakers > 0 or ts.max_speakers > 0).lower(),
        }
        if ts.language and ts.language != "auto":
            data["language"] = ts.language
        if ts.model:
            data["model"] = ts.model
        if ts.initial_prompt:
            data["prompt"] = ts.initial_prompt
        if ts.hotwords:
            data["hotwords"] = ts.hotwords

        async with httpx.AsyncClient(timeout=600) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files={"file": f},
                    data=data,
                )
            response.raise_for_status()
            result = response.json()

        segments = result.get("segments", [])
        utterances = [
            Utterance(
                start=int(seg.get("start", 0) * 1000),
                end=int(seg.get("end", 0) * 1000),
                text=seg.get("text", "").strip(),
                speaker=seg.get("speaker"),
            )
            for seg in segments
        ]

        return TranscriptionResult(
            id="", status="completed", utterances=utterances,
            text=result.get("text", ""), language=result.get("language"),
        )

    async def get_status(self, job_id: str) -> TranscriptionStatus:
        status = _statuses.get(job_id, "pending")
        return TranscriptionStatus(id=job_id, status=status)

    async def get_result(self, job_id: str) -> TranscriptionResult:
        result = _results.get(job_id)
        if not result:
            raise ValueError(f"No result for job {job_id}")
        result.id = job_id
        return result
