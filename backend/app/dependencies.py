from fastapi import HTTPException, Request
from app.config import settings
from app.models import UserInfo


async def get_current_user(request: Request) -> UserInfo:
    user_id = request.headers.get("X-Auth-Request-User")
    email = request.headers.get("X-Auth-Request-Email")

    if user_id:
        return UserInfo(id=user_id, email=email)
    elif email:
        return UserInfo(id=email, email=email)
    elif settings.DEV_MODE:
        return UserInfo(id="dev-user", email="dev@localhost")
    else:
        raise HTTPException(status_code=401, detail="Missing authentication headers")
