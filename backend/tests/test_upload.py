import pytest
from unittest.mock import patch, AsyncMock
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
async def test_upload_webm_file():
    """WebM files should be accepted for browser recordings."""
    transport = ASGITransport(app=app)
    with patch("app.routers.upload.convert_to_mp3", new_callable=AsyncMock) as mock_convert:
        mock_convert.return_value = "/tmp/fake.mp3"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/upload",
                files={"file": ("test.webm", b"\x1a\x45\xdf\xa3" + b"\x00" * 100, "audio/webm")},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "test.webm"
    assert data["media_type"] == "webm"


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
