from abc import ABC, abstractmethod
from app.models import SummaryResult, ProtocolResult, LLMRefinementResponse


class LLMProvider(ABC):
    @abstractmethod
    async def generate_summary(self, transcript: str, chapter_hints: list | None = None, language: str | None = None) -> SummaryResult:
        """Generate a summary with chapters from timestamped transcript text."""

    @abstractmethod
    async def generate_protocol(self, transcript: str, summary_context: str | None = None, language: str | None = None) -> ProtocolResult:
        """Generate a meeting protocol from timestamped transcript text."""

    @abstractmethod
    async def generate_refinement(self, transcript: str, context: str | None = None) -> LLMRefinementResponse:
        ...

    @abstractmethod
    async def generate_title(self, transcript: str) -> str:
        """Generate a short title from transcript text."""
