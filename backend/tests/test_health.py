import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_config_reports_api_tokens_enabled(monkeypatch):
    from app import config as config_module
    monkeypatch.setattr(config_module.settings, "ENABLE_API_TOKENS", True)
    # Also patch the reference held by the config router module to survive any
    # `importlib.reload(config_module)` in test_config.py.
    from app.routers import config_router as cr
    monkeypatch.setattr(cr.settings, "ENABLE_API_TOKENS", True)
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/config")
    assert r.status_code == 200
    assert r.json()["api_tokens_enabled"] is True
