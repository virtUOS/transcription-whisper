import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ASR_BACKEND: str = os.getenv("ASR_BACKEND", "murmurai")
    ASR_URL: str = os.getenv("ASR_URL", "http://localhost:8880")
    ASR_API_KEY: str = os.getenv("ASR_API_KEY", "")
    ASR_MAX_CONCURRENT: int = int(os.getenv("ASR_MAX_CONCURRENT", "3"))

    WHISPER_MODELS: list[str] = os.getenv("WHISPER_MODELS", "base,large-v3,large-v3-turbo").split(",")
    DEFAULT_WHISPER_MODEL: str = os.getenv("DEFAULT_WHISPER_MODEL", "base")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")

    TEMP_PATH: str = os.getenv("TEMP_PATH", "tmp/transcription-files")
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    LOGOUT_URL: str = os.getenv("LOGOUT_URL", "")
    DEFAULT_EXPIRY_HOURS: int = int(os.getenv("DEFAULT_EXPIRY_HOURS", "72"))
    ARCHIVE_EXPIRY_HOURS: int = int(os.getenv("ARCHIVE_EXPIRY_HOURS", "4320"))
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "")

    POPULAR_LANGUAGES: list[str] = os.getenv("POPULAR_LANGUAGES", "de,en,es,fr").split(",")
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() in ("true", "1", "yes")
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")

    @property
    def db_path(self) -> str:
        if self.DATABASE_PATH:
            return self.DATABASE_PATH
        return os.path.join(self.TEMP_PATH, "transcription.db")


settings = Settings()
