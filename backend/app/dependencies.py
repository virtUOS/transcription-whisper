from fastapi import Request
from app.models import UserInfo


async def get_current_user(request: Request) -> UserInfo:
    user_id = request.headers.get("X-Forwarded-User")
    email = request.headers.get("X-Forwarded-Email")

    if user_id:
        return UserInfo(id=user_id, email=email)
    elif email:
        return UserInfo(id=email, email=email)
    else:
        return UserInfo(id="anonymous")
