import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.asr.murmurai import MurmurAIBackend
from app.services.asr.base import TranscriptionSettings

@pytest.mark.asyncio
async def test_submit_sends_correct_params():
    backend = MurmurAIBackend()
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "job-123"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.asr.murmurai.httpx.AsyncClient") as MockClient, \
         patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=b""), __exit__=MagicMock(return_value=False)))):
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        settings_obj = TranscriptionSettings(language="de", model="large-v3", min_speakers=1, max_speakers=4)
        job_id = await backend.submit("/fake/path.mp3", settings_obj)

    assert job_id == "job-123"
    call_kwargs = mock_client.post.call_args
    assert "language_code" in call_kwargs.kwargs.get("data", {})

@pytest.mark.asyncio
async def test_get_status_maps_murmurai_status():
    backend = MurmurAIBackend()
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "processing"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.asr.murmurai.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        status = await backend.get_status("job-123")

    assert status.status == "processing"


def _cleanup_errors():
    from prometheus_client import REGISTRY
    return REGISTRY.get_sample_value(
        "transcription_errors_total", {"error_type": "asr_cleanup_failed", "component": "asr"},
    ) or 0.0


@pytest.mark.asyncio
async def test_cleanup_deletes_the_remote_transcript():
    """MurmurAI keeps every transcript until told otherwise; cleanup() tells it."""
    backend = MurmurAIBackend()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.asr.murmurai.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.delete.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        await backend.cleanup("job-123")

    mock_client.delete.assert_awaited_once_with(
        f"{backend.base_url}/v1/transcript/job-123", headers=backend.headers,
    )


@pytest.mark.asyncio
async def test_cleanup_failure_is_counted_not_raised():
    """A failed remote delete must never fail the transcription that already succeeded."""
    import httpx
    backend = MurmurAIBackend()

    with patch("app.services.asr.murmurai.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.delete.side_effect = httpx.ConnectError("asr down")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        before = _cleanup_errors()
        await backend.cleanup("job-123")

    assert _cleanup_errors() == before + 1
