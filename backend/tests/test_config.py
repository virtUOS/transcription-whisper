import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_config_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "whisper_models" in data
    assert "asr_backend" in data


@pytest.mark.asyncio
async def test_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
    assert response.status_code == 200
    assert "transcription_app_info" in response.text


import importlib
import os


def test_api_token_settings_defaults(monkeypatch):
    # Neutralize the repo .env so reload() sees only the shell environment,
    # otherwise a local developer .env with ENABLE_API_TOKENS=true leaks in.
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: None)
    from app import config as config_module
    for var in ("ENABLE_API_TOKENS", "API_TOKEN_MAX_PER_USER", "API_TOKEN_DEFAULT_EXPIRY_DAYS"):
        monkeypatch.delenv(var, raising=False)
    importlib.reload(config_module)
    assert config_module.settings.ENABLE_API_TOKENS is False
    assert config_module.settings.API_TOKEN_MAX_PER_USER == 10
    assert config_module.settings.API_TOKEN_DEFAULT_EXPIRY_DAYS == 90


def test_api_token_settings_from_env(monkeypatch):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: None)
    from app import config as config_module
    monkeypatch.setenv("ENABLE_API_TOKENS", "true")
    monkeypatch.setenv("API_TOKEN_MAX_PER_USER", "5")
    monkeypatch.setenv("API_TOKEN_DEFAULT_EXPIRY_DAYS", "30")
    importlib.reload(config_module)
    assert config_module.settings.ENABLE_API_TOKENS is True
    assert config_module.settings.API_TOKEN_MAX_PER_USER == 5
    assert config_module.settings.API_TOKEN_DEFAULT_EXPIRY_DAYS == 30
