"""llm_requests_total counts attempts, so errors / requests is the failure ratio.

Before this only successes were counted: a refinement that failed twice with
no success showed requests=1 (a stale series) and errors=2 — more errors than
requests — and the alert rule had to use requests + errors as its denominator.
The alert and dashboard in transcription-whisper-ansible change with this.
"""
import pytest
from fastapi import HTTPException
from prometheus_client import REGISTRY

from app.config import settings
from app.metrics import measure_llm_operation


def _value(name, operation):
    return REGISTRY.get_sample_value(
        name, {"provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL, "operation": operation},
    ) or 0.0


@pytest.mark.asyncio
async def test_a_successful_call_counts_one_request_and_no_error():
    op = "count-test-ok"
    r0, e0 = _value("transcription_llm_requests_total", op), _value("transcription_llm_errors_total", op)
    async with measure_llm_operation(op):
        pass
    assert _value("transcription_llm_requests_total", op) == r0 + 1
    assert _value("transcription_llm_errors_total", op) == e0


@pytest.mark.asyncio
async def test_a_failed_call_counts_one_request_and_one_error():
    op = "count-test-fail"
    r0, e0 = _value("transcription_llm_requests_total", op), _value("transcription_llm_errors_total", op)
    with pytest.raises(RuntimeError):
        async with measure_llm_operation(op):
            raise RuntimeError("boom")
    assert _value("transcription_llm_requests_total", op) == r0 + 1
    assert _value("transcription_llm_errors_total", op) == e0 + 1


@pytest.mark.asyncio
async def test_an_http_exception_counts_neither():
    op = "count-test-http"
    r0, e0 = _value("transcription_llm_requests_total", op), _value("transcription_llm_errors_total", op)
    with pytest.raises(HTTPException):
        async with measure_llm_operation(op):
            raise HTTPException(status_code=503)
    assert _value("transcription_llm_requests_total", op) == r0
    assert _value("transcription_llm_errors_total", op) == e0
