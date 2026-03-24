from abc import ABC, abstractmethod
from app.models import TranscriptionStatus, TranscriptionResult


class TranscriptionSettings:
    def __init__(self, language=None, model="base", min_speakers=0, max_speakers=0, initial_prompt=None, hotwords=None):
        self.language = language
        self.model = model
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        self.initial_prompt = initial_prompt
        self.hotwords = hotwords


class ASRBackend(ABC):
    @abstractmethod
    async def submit(self, file_path: str, settings: TranscriptionSettings) -> str:
        """Submit a transcription job. Returns backend-specific job ID."""

    @abstractmethod
    async def get_status(self, job_id: str) -> TranscriptionStatus:
        """Get job status."""

    @abstractmethod
    async def get_result(self, job_id: str) -> TranscriptionResult:
        """Get the transcription result."""
