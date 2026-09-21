"""Title generation must go through measure_llm_operation like the other LLM
operations. It called the provider directly, so title calls counted tokens but
never a request, error or duration: three of the four LLM panels and the
failure-ratio alert could not see them.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from prometheus_client import REGISTRY

from app.config import settings
from app.routers.transcription import _generate_title


def _value(name):
    return REGISTRY.get_sample_value(
        name, {"provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL, "operation": "title"},
    ) or 0.0


@pytest.mark.asyncio
async def test_successful_title_counts_a_request_and_a_duration():
    provider = MagicMock()
    provider.generate_title = AsyncMock(return_value="A title")
    r0, d0 = _value("transcription_llm_requests_total"), _value("transcription_llm_duration_seconds_count")

    assert await _generate_title(provider, "hello world") == "A title"

    assert _value("transcription_llm_requests_total") == r0 + 1
    assert _value("transcription_llm_duration_seconds_count") == d0 + 1


@pytest.mark.asyncio
async def test_failed_title_counts_a_request_and_an_error_and_reraises():
    provider = MagicMock()
    provider.generate_title = AsyncMock(side_effect=RuntimeError("boom"))
    r0, e0 = _value("transcription_llm_requests_total"), _value("transcription_llm_errors_total")

    with pytest.raises(RuntimeError):
        await _generate_title(provider, "hello world")

    assert _value("transcription_llm_requests_total") == r0 + 1
    assert _value("transcription_llm_errors_total") == e0 + 1
