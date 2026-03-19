from abc import ABC, abstractmethod
from app.models import SummaryResult, ProtocolResult


class LLMProvider(ABC):
    @abstractmethod
    async def generate_summary(self, transcript: str) -> SummaryResult:
        """Generate a summary with chapters from timestamped transcript text."""

    @abstractmethod
    async def generate_protocol(self, transcript: str, summary_context: str | None = None) -> ProtocolResult:
        """Generate a meeting protocol from timestamped transcript text."""
