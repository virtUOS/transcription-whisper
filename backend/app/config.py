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
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "ffprobe")
    LOGOUT_URL: str = os.getenv("LOGOUT_URL", "")
    CONTACT_EMAIL: str = os.getenv("CONTACT_EMAIL", "")
    DEFAULT_EXPIRY_HOURS: int = int(os.getenv("DEFAULT_EXPIRY_HOURS", "72"))
    ARCHIVE_EXPIRY_HOURS: int = int(os.getenv("ARCHIVE_EXPIRY_HOURS", "4320"))
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "")

    POPULAR_LANGUAGES: list[str] = os.getenv("POPULAR_LANGUAGES", "de,en,es,fr").split(",")
    ENABLED_LANGUAGES: list[str] = [c.strip() for c in os.getenv("ENABLED_LANGUAGES", "").split(",") if c.strip()]
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() in ("true", "1", "yes")
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")
    ENABLE_API_TOKENS: bool = os.getenv("ENABLE_API_TOKENS", "false").lower() in ("true", "1", "yes")
    API_TOKEN_MAX_PER_USER: int = int(os.getenv("API_TOKEN_MAX_PER_USER", "10"))
    API_TOKEN_DEFAULT_EXPIRY_DAYS: int = int(os.getenv("API_TOKEN_DEFAULT_EXPIRY_DAYS", "90"))

    INVITATION_MODE: bool = os.getenv("INVITATION_MODE", "false").lower() in ("true", "1", "yes")
    ADMIN_EMAILS: list[str] = [
        e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()
    ]
    INVITATION_EXPIRY_DAYS: int = int(os.getenv("INVITATION_EXPIRY_DAYS", "7"))

    KEYCLOAK_ADMIN_URL: str = os.getenv("KEYCLOAK_ADMIN_URL", "")
    KEYCLOAK_ADMIN_REALM: str = os.getenv("KEYCLOAK_ADMIN_REALM", "master")
    KEYCLOAK_TARGET_REALM: str = os.getenv("KEYCLOAK_TARGET_REALM", "")
    KEYCLOAK_ADMIN_CLIENT_ID: str = os.getenv("KEYCLOAK_ADMIN_CLIENT_ID", "admin-cli")
    KEYCLOAK_ADMIN_CLIENT_SECRET: str = os.getenv("KEYCLOAK_ADMIN_CLIENT_SECRET", "")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")

    APP_PUBLIC_URL: str = os.getenv("APP_PUBLIC_URL", "")

    @property
    def db_path(self) -> str:
        if self.DATABASE_PATH:
            return self.DATABASE_PATH
        return os.path.join(self.TEMP_PATH, "transcription.db")


settings = Settings()
