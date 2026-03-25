import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, Request
from app.dependencies import get_current_user


@pytest.mark.asyncio
async def test_get_user_from_auth_request_header():
    request = MagicMock(spec=Request)
    request.headers = {"X-Auth-Request-User": "jdoe"}
    user = await get_current_user(request)
    assert user.id == "jdoe"


@pytest.mark.asyncio
async def test_get_user_from_email_header():
    request = MagicMock(spec=Request)
    request.headers = {"X-Auth-Request-Email": "jdoe@uni.de"}
    user = await get_current_user(request)
    assert user.id == "jdoe@uni.de"
    assert user.email == "jdoe@uni.de"


@pytest.mark.asyncio
async def test_missing_auth_headers_raises_401():
    request = MagicMock(spec=Request)
    request.headers = {}
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request)
    assert exc_info.value.status_code == 401
