import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.asr.whisperx import WhisperXBackend
from app.services.asr.base import TranscriptionSettings

@pytest.mark.asyncio
async def test_submit_sends_correct_params():
    backend = WhisperXBackend()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "text": "Hello world",
        "segments": [{"start": 0.0, "end": 2.0, "text": "Hello world", "speaker": "SPEAKER_00"}],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.asr.whisperx.httpx.AsyncClient") as MockClient, \
         patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=b""), __exit__=MagicMock(return_value=False)))):
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        settings_obj = TranscriptionSettings(language="de", model="large-v3")
        job_id = await backend.submit("/fake/path.mp3", settings_obj)

    assert job_id is not None
    status = await backend.get_status(job_id)
    assert status.status == "completed"

@pytest.mark.asyncio
async def test_get_result_returns_utterances():
    backend = WhisperXBackend()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "text": "Hello world",
        "segments": [{"start": 0.0, "end": 2.0, "text": "Hello world", "speaker": "SPEAKER_00"}],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.asr.whisperx.httpx.AsyncClient") as MockClient, \
         patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=b""), __exit__=MagicMock(return_value=False)))):
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        settings_obj = TranscriptionSettings(language="de")
        job_id = await backend.submit("/fake/path.mp3", settings_obj)

    result = await backend.get_result(job_id)
    assert len(result.utterances) == 1
    assert result.utterances[0].text == "Hello world"
    assert result.utterances[0].start == 0
    assert result.utterances[0].end == 2000
