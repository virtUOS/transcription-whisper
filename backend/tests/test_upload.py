import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_upload_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake mp3 content", "audio/mpeg")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["original_filename"] == "test.mp3"
    assert data["media_type"] == "mp3"


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"not audio", "text/plain")},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_media_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload first
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake mp3 content", "audio/mpeg")},
        )
        file_id = upload_resp.json()["id"]

        # Retrieve media
        response = await client.get(f"/api/media/{file_id}")
    assert response.status_code == 200
