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
async def test_cleanup_failure_is_counted_not_raised(capsys):
    """A failed remote delete must never fail the transcription that already succeeded."""
    import httpx
    backend = MurmurAIBackend()

    with patch("app.services.asr.murmurai.httpx.AsyncClient") as MockClient, \
         patch("app.services.asr.murmurai.CLEANUP_RETRY_DELAYS", (0, 0)):
        mock_client = AsyncMock()
        mock_client.delete.side_effect = httpx.ConnectError("asr down")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        before = _cleanup_errors()
        await backend.cleanup("job-123")

    assert _cleanup_errors() == before + 1
    # Logged, not printed: the hourly cleanup prints "Cleanup error:" for its own failures
    assert capsys.readouterr().out == ""


def _delete_client(*responses):
    """An httpx.AsyncClient mock whose successive DELETEs return `responses`."""
    mock_client = AsyncMock()
    mock_client.delete.side_effect = list(responses)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _response(status_code):
    import httpx
    return httpx.Response(status_code, request=httpx.Request("DELETE", "http://asr/v1/transcript/job-123"))


async def _cleanup_with(*responses):
    backend = MurmurAIBackend()
    mock_client = _delete_client(*responses)
    with patch("app.services.asr.murmurai.httpx.AsyncClient", return_value=mock_client), \
         patch("app.services.asr.murmurai.CLEANUP_RETRY_DELAYS", (0, 0)):
        before = _cleanup_errors()
        await backend.cleanup("job-123")
    return mock_client.delete.await_count, _cleanup_errors() - before


@pytest.mark.asyncio
async def test_cleanup_retries_then_succeeds():
    calls, errors = await _cleanup_with(_response(500), _response(200))
    assert (calls, errors) == (2, 0)


@pytest.mark.asyncio
async def test_cleanup_404_is_success():
    calls, errors = await _cleanup_with(_response(404))
    assert (calls, errors) == (1, 0)


@pytest.mark.asyncio
async def test_cleanup_gives_up_after_three():
    calls, errors = await _cleanup_with(_response(500), _response(500), _response(500))
    assert (calls, errors) == (3, 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403])
async def test_cleanup_client_error_is_not_retried(status_code):
    """A retry cannot fix a rejected request, only an unreachable or failing server."""
    calls, errors = await _cleanup_with(_response(status_code))
    assert (calls, errors) == (1, 1)
