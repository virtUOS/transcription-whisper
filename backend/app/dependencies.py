import asyncio
import logging

from fastapi import HTTPException, Request

from app.config import settings
from app.database import get_db
from app.metrics import inc, auth_failures_total, api_token_auth_total
from app.models import UserInfo
from app.services.api_tokens import resolve_token, touch_last_used

logger = logging.getLogger(__name__)


async def _touch_best_effort(token_id: str) -> None:
    try:
        async with get_db() as db:
            await touch_last_used(db, token_id=token_id)
    except Exception as e:
        logger.warning("touch_last_used failed for %s: %s", token_id, e)


async def get_current_user(request: Request) -> UserInfo:
    if settings.ENABLE_API_TOKENS:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer tw_"):
            raw = auth.removeprefix("Bearer ").strip()
            async with get_db() as db:
                result = await resolve_token(db, raw_token=raw)
            if result is not None:
                user, token_id = result
                inc(api_token_auth_total, "success")
                asyncio.create_task(_touch_best_effort(token_id))
                return user
            inc(api_token_auth_total, "failure")
            inc(auth_failures_total, "invalid_token")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API token",
                headers={"WWW-Authenticate": 'Bearer realm="transcription-whisper"'},
            )

    user_id = request.headers.get("X-Auth-Request-User")
    email = request.headers.get("X-Auth-Request-Email")
    if user_id:
        return UserInfo(id=user_id, email=email)
    if email:
        return UserInfo(id=email, email=email)
    if settings.DEV_MODE:
        return UserInfo(id="dev-user", email="dev@localhost")

    inc(auth_failures_total, "missing_headers")
    raise HTTPException(status_code=401, detail="Missing authentication headers")
