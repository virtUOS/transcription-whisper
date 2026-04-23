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


def test_invitation_config_defaults(monkeypatch):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: None)
    from app import config as config_module
    # Ensure env is clean, then reload settings
    for key in [
        "INVITATION_MODE", "ADMIN_EMAILS",
        "KEYCLOAK_ADMIN_URL", "KEYCLOAK_ADMIN_REALM",
        "KEYCLOAK_TARGET_REALM", "KEYCLOAK_ADMIN_CLIENT_ID",
        "KEYCLOAK_ADMIN_CLIENT_SECRET",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_STARTTLS",
        "APP_PUBLIC_URL", "INVITATION_EXPIRY_DAYS",
    ]:
        monkeypatch.delenv(key, raising=False)
    importlib.reload(config_module)
    s = config_module.settings
    assert s.INVITATION_MODE is False
    assert s.ADMIN_EMAILS == []
    assert s.KEYCLOAK_ADMIN_URL == ""
    assert s.KEYCLOAK_ADMIN_REALM == "master"
    assert s.KEYCLOAK_TARGET_REALM == ""
    assert s.KEYCLOAK_ADMIN_CLIENT_ID == "admin-cli"
    assert s.KEYCLOAK_ADMIN_CLIENT_SECRET == ""
    assert s.SMTP_HOST == ""
    assert s.SMTP_USER == ""
    assert s.SMTP_PASSWORD == ""
    assert s.SMTP_PORT == 587
    assert s.SMTP_FROM == ""
    assert s.SMTP_STARTTLS is True
    assert s.APP_PUBLIC_URL == ""
    assert s.INVITATION_EXPIRY_DAYS == 7


def test_admin_emails_lowercased_and_trimmed(monkeypatch):
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: None)
    from app import config as config_module
    monkeypatch.delenv("ADMIN_EMAILS", raising=False)
    monkeypatch.setenv("ADMIN_EMAILS", "Alice@Example.com, bob@example.com ")
    importlib.reload(config_module)
    s = config_module.settings
    assert s.ADMIN_EMAILS == ["alice@example.com", "bob@example.com"]
