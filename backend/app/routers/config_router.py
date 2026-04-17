from fastapi import APIRouter
from app.config import settings
from app.models import ConfigResponse
from app.metrics import metrics_response

router = APIRouter()


@router.get("/api/health")
async def health():
    return {"status": "healthy"}


@router.get("/api/config", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        asr_backend=settings.ASR_BACKEND,
        whisper_models=settings.WHISPER_MODELS,
        default_model=settings.DEFAULT_WHISPER_MODEL,
        llm_available=bool(settings.LLM_PROVIDER),
        logout_url=settings.LOGOUT_URL,
        popular_languages=settings.POPULAR_LANGUAGES,
        enabled_languages=settings.ENABLED_LANGUAGES,
        api_tokens_enabled=settings.ENABLE_API_TOKENS,
        api_token_default_expiry_days=settings.API_TOKEN_DEFAULT_EXPIRY_DAYS,
    )


@router.get("/metrics")
async def get_metrics():
    return metrics_response()
