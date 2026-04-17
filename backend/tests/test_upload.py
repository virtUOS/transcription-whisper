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
        mock_convert.assert_called_once()


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


@pytest.mark.asyncio
async def test_rename_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload first
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake mp3 content", "audio/mpeg")},
        )
        file_id = upload_resp.json()["id"]

        # Rename
        response = await client.patch(
            f"/api/files/{file_id}/rename",
            json={"filename": "my-meeting"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "my-meeting.mp3"
    assert data["id"] == file_id


@pytest.mark.asyncio
async def test_rename_file_empty_name():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake mp3 content", "audio/mpeg")},
        )
        file_id = upload_resp.json()["id"]

        response = await client.patch(
            f"/api/files/{file_id}/rename",
            json={"filename": "   "},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_rename_file_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            "/api/files/nonexistent/rename",
            json={"filename": "new-name"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rename_preserves_extension():
    transport = ASGITransport(app=app)
    with patch("app.routers.upload.convert_to_mp3", new_callable=AsyncMock) as mock_convert:
        mock_convert.return_value = "/tmp/fake.mp3"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            upload_resp = await client.post(
                "/api/upload",
                files={"file": ("recording.webm", b"\x1a\x45\xdf\xa3" + b"\x00" * 100, "audio/webm")},
            )
            file_id = upload_resp.json()["id"]

            response = await client.patch(
                f"/api/files/{file_id}/rename",
                json={"filename": "team-standup"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "team-standup.webm"


@pytest.mark.asyncio
async def test_rename_strips_caller_supplied_extension():
    # "meeting.webm" + original ".webm" must not become "meeting.webm.webm".
    transport = ASGITransport(app=app)
    with patch("app.routers.upload.convert_to_mp3", new_callable=AsyncMock) as mock_convert:
        mock_convert.return_value = "/tmp/fake.mp3"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            upload_resp = await client.post(
                "/api/upload",
                files={"file": ("recording.webm", b"\x1a\x45\xdf\xa3" + b"\x00" * 100, "audio/webm")},
            )
            file_id = upload_resp.json()["id"]

            response = await client.patch(
                f"/api/files/{file_id}/rename",
                json={"filename": "meeting.webm"},
            )
    assert response.status_code == 200
    assert response.json()["original_filename"] == "meeting.webm"


@pytest.mark.asyncio
async def test_upload_mp3_has_video_false():
    """Audio files should have has_video=False."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.mp3", b"fake mp3 content", "audio/mpeg")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["has_video"] is False


@pytest.mark.asyncio
async def test_upload_with_has_video_param():
    """Recorder can pass has_video query param to skip ffprobe."""
    transport = ASGITransport(app=app)
    with patch("app.routers.upload.convert_to_mp3", new_callable=AsyncMock) as mock_convert:
        mock_convert.return_value = "/tmp/fake.mp3"
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/upload?has_video=false",
                files={"file": ("recording.webm", b"\x1a\x45\xdf\xa3" + b"\x00" * 100, "audio/webm")},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["has_video"] is False


@pytest.mark.asyncio
async def test_upload_with_has_video_true():
    """Recorder with camera passes has_video=true."""
    transport = ASGITransport(app=app)
    with patch("app.routers.upload.convert_to_mp3", new_callable=AsyncMock) as mock_convert, \
         patch("app.routers.upload.has_video_stream", new_callable=AsyncMock) as mock_detect:
        mock_convert.return_value = "/tmp/fake.mp3"
        mock_detect.return_value = True
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/upload?has_video=true",
                files={"file": ("recording.webm", b"\x1a\x45\xdf\xa3" + b"\x00" * 100, "audio/webm")},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["has_video"] is True
