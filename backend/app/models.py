from pydantic import BaseModel, field_validator, model_validator


class ErrorResponse(BaseModel):
    error: str
    detail: str


class UserInfo(BaseModel):
    id: str
    email: str | None = None


class FileInfo(BaseModel):
    id: str
    original_filename: str
    media_type: str
    file_size: int


class TranscriptionSettings(BaseModel):
    file_id: str
    language: str | None = None
    model: str = "base"
    min_speakers: int = 0
    max_speakers: int = 0
    initial_prompt: str | None = None
    hotwords: str | None = None


class TranscriptionStatus(BaseModel):
    id: str
    status: str
    progress: float | None = None
    error: str | None = None


class Utterance(BaseModel):
    start: int
    end: int
    text: str
    speaker: str | None = None


class TranscriptionResult(BaseModel):
    id: str
    status: str
    utterances: list[Utterance] = []
    text: str = ""
    language: str | None = None


class TranscriptionListItem(BaseModel):
    id: str
    file_id: str
    original_filename: str
    status: str
    language: str | None = None
    model: str | None = None
    created_at: str
    file_size: int = 0
    expires_at: str
    archived: bool = False
    title: str | None = None


class SpeakerMappingRequest(BaseModel):
    mappings: dict[str, str]  # {"Speaker 1": "Dr. Mueller"}


class RenameRequest(BaseModel):
    filename: str


class TitleRequest(BaseModel):
    title: str


class ChapterHint(BaseModel):
    title: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ChapterHint":
        if not self.title and not self.description:
            raise ValueError("At least one of title or description must be provided")
        return self


class SummarizeRequest(BaseModel):
    chapter_hints: list[ChapterHint] | None = None
    language: str | None = None

    @field_validator("chapter_hints")
    @classmethod
    def max_hints(cls, v: list[ChapterHint] | None) -> list[ChapterHint] | None:
        if v and len(v) > 30:
            raise ValueError("Maximum 30 chapter hints allowed")
        return v


class SummaryChapter(BaseModel):
    title: str
    start_time: int
    end_time: int
    summary: str


class SummaryResult(BaseModel):
    summary: str
    chapters: list[SummaryChapter]
    chapter_hints: list[ChapterHint] | None = None
    language: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None


class ProtocolRequest(BaseModel):
    language: str | None = None


class ProtocolKeyPoint(BaseModel):
    topic: str
    speaker: str
    timestamp: int | None  # milliseconds, null if not determinable
    content: str


class ProtocolDecision(BaseModel):
    decision: str
    timestamp: int | None  # milliseconds, null if not determinable


class ProtocolActionItem(BaseModel):
    task: str
    assignee: str
    timestamp: int | None  # milliseconds, null if not determinable


class ProtocolResult(BaseModel):
    title: str
    participants: list[str]
    key_points: list[ProtocolKeyPoint]
    decisions: list[ProtocolDecision]
    action_items: list[ProtocolActionItem]
    language: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None


class RefineRequest(BaseModel):
    context: str | None = None


class LLMRefinementResponse(BaseModel):
    """Raw response from LLM provider — no provider/model metadata."""
    utterances: list[Utterance]
    changes_summary: str


class RefinementMetadata(BaseModel):
    """Assembled by the router after the LLM call."""
    changed_indices: list[int]
    changes_summary: str
    context: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    created_at: str | None = None


class RefinementResult(BaseModel):
    """Full response returned to the frontend."""
    utterances: list[Utterance]
    metadata: RefinementMetadata


class AnalysisRequest(BaseModel):
    template: str | None = "summary"
    custom_prompt: str | None = None
    language: str | None = None
    chapter_hints: list[ChapterHint] | None = None
    agenda: str | None = None


class TranslationRequest(BaseModel):
    target_language: str


class ConfigResponse(BaseModel):
    asr_backend: str
    whisper_models: list[str]
    default_model: str
    llm_available: bool
    logout_url: str
