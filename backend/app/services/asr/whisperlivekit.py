import asyncio
import uuid
import httpx
from app.config import settings
from app.services.asr.base import ASRBackend, TranscriptionSettings
from app.models import TranscriptionStatus, TranscriptionResult, Utterance

_semaphore = asyncio.Semaphore(settings.ASR_MAX_CONCURRENT)

# In-memory cache for WhisperLiveKit results. Same synchronous pattern as
# WhisperX — submit() blocks until the HTTP call completes, result is stored
# in the DB by _run_transcription() right after submit() returns.
_results: dict[str, TranscriptionResult] = {}
_statuses: dict[str, str] = {}


class WhisperLiveKitBackend(ASRBackend):
    def __init__(self):
        self.base_url = settings.ASR_URL

    async def submit(self, file_path: str, ts: TranscriptionSettings) -> str:
        job_id = str(uuid.uuid4())
        _statuses[job_id] = "processing"

        async with _semaphore:
            try:
                result = await self._call_whisperlivekit(file_path, ts)
                _results[job_id] = result
                _statuses[job_id] = "completed"
            except Exception as e:
                _statuses[job_id] = "failed"
                _results[job_id] = TranscriptionResult(
                    id=job_id, status="failed", text="", utterances=[], language=None
                )
                raise

        return job_id

    async def _call_whisperlivekit(self, file_path: str, ts: TranscriptionSettings) -> TranscriptionResult:
        data = {"response_format": "verbose_json"}
        if ts.language and ts.language != "auto":
            data["language"] = ts.language
        if ts.initial_prompt:
            data["prompt"] = ts.initial_prompt

        async with httpx.AsyncClient(timeout=600) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    files={"file": f},
                    data=data,
                )
            response.raise_for_status()
            result = response.json()

        utterances = self._words_to_utterances(result)

        return TranscriptionResult(
            id="", status="completed", utterances=utterances,
            text=result.get("text", ""), language=result.get("language"),
        )

    @staticmethod
    def _words_to_utterances(result: dict) -> list[Utterance]:
        """Build sentence-level utterances from word timestamps.

        WLK's REST endpoint often returns a single segment for the whole audio.
        We split on sentence-ending punctuation using the word-level timestamps
        to produce finer-grained utterances similar to WhisperX output.
        Falls back to segment-level if no words are available.
        """
        words = result.get("words", [])
        if not words:
            # Fallback to segments
            return [
                Utterance(
                    start=int(seg.get("start", 0) * 1000),
                    end=int(seg.get("end", 0) * 1000),
                    text=seg.get("text", "").strip(),
                    speaker=None,
                )
                for seg in result.get("segments", [])
            ]

        sentence_endings = {".", "!", "?"}
        utterances: list[Utterance] = []
        current_words: list[dict] = []

        for word in words:
            current_words.append(word)
            text = word.get("word", "")
            # Split when word ends with sentence-ending punctuation
            if text and text.rstrip()[-1] in sentence_endings:
                utt_text = " ".join(w.get("word", "") for w in current_words).strip()
                if utt_text:
                    utterances.append(Utterance(
                        start=int(current_words[0].get("start", 0) * 1000),
                        end=int(current_words[-1].get("end", 0) * 1000),
                        text=utt_text,
                        speaker=(
                            f"Speaker {s}" if (s := current_words[0].get("speaker")) is not None and s != -2
                            else None
                        ),
                    ))
                current_words = []

        # Remaining words that didn't end with punctuation
        if current_words:
            utt_text = " ".join(w.get("word", "") for w in current_words).strip()
            if utt_text:
                utterances.append(Utterance(
                    start=int(current_words[0].get("start", 0) * 1000),
                    end=int(current_words[-1].get("end", 0) * 1000),
                    text=utt_text,
                    speaker=None,
                ))

        return utterances

    async def get_status(self, job_id: str) -> TranscriptionStatus:
        status = _statuses.get(job_id, "pending")
        return TranscriptionStatus(id=job_id, status=status)

    async def get_result(self, job_id: str) -> TranscriptionResult:
        result = _results.get(job_id)
        if not result:
            raise ValueError(f"No result for job {job_id}")
        result.id = job_id
        # Clean up in-memory cache after retrieval
        _results.pop(job_id, None)
        _statuses.pop(job_id, None)
        return result
