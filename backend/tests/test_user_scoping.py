import pytest
from unittest.mock import MagicMock
from fastapi import Request
from app.dependencies import get_current_user


@pytest.mark.asyncio
async def test_get_user_from_forwarded_header():
    request = MagicMock(spec=Request)
    request.headers = {"X-Forwarded-User": "jdoe"}
    user = await get_current_user(request)
    assert user.id == "jdoe"


@pytest.mark.asyncio
async def test_get_user_from_email_header():
    request = MagicMock(spec=Request)
    request.headers = {"X-Forwarded-Email": "jdoe@uni.de"}
    user = await get_current_user(request)
    assert user.id == "jdoe@uni.de"
    assert user.email == "jdoe@uni.de"


@pytest.mark.asyncio
async def test_get_user_anonymous_fallback():
    request = MagicMock(spec=Request)
    request.headers = {}
    user = await get_current_user(request)
    assert user.id == "anonymous"
