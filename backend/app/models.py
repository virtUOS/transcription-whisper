from pydantic import BaseModel


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


class SpeakerMappingRequest(BaseModel):
    mappings: dict[str, str]  # {"Speaker 1": "Dr. Mueller"}


class SummaryChapter(BaseModel):
    title: str
    start_time: int
    end_time: int
    summary: str


class SummaryResult(BaseModel):
    summary: str
    chapters: list[SummaryChapter]
    llm_provider: str | None = None
    llm_model: str | None = None


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
    llm_provider: str | None = None
    llm_model: str | None = None


class ConfigResponse(BaseModel):
    asr_backend: str
    whisper_models: list[str]
    default_model: str
    llm_available: bool
    logout_url: str
