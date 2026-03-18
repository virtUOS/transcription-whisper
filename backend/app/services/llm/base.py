from abc import ABC, abstractmethod
from app.models import SummaryResult


class LLMProvider(ABC):
    @abstractmethod
    async def generate_summary(self, transcript: str) -> SummaryResult:
        """Generate a summary with chapters from timestamped transcript text."""
