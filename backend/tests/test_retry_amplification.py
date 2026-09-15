"""Retry layers must not multiply.

Measured in production: a chunk call returned APITimeoutError after 1082s
against a 360s timeout — the SDK had silently retried it three times
(360 x (max_retries 2 + 1)). Layering the app's own per-chunk retry on top of
that multiplies rather than adds: at a 600s timeout it would be
600 x 3 x 3 = 90 minutes for a single chunk.

The app's retry is the one to keep: it re-validates the utterance count, which
the SDK's blind re-send does not.
"""
from app.config import settings
from app.services.llm.base import CHUNK_ERROR_RETRIES, CHUNK_COUNT_RETRIES


def test_sdk_retries_are_not_layered_under_the_apps_own_retry():
    assert settings.LLM_MAX_RETRIES == 0, (
        "the SDK must not retry underneath chunked_utterance_call's retry; "
        "two layers multiply into hours of worst-case wall clock"
    )


def test_worst_case_for_one_chunk_stays_bounded():
    """A chunk must not be able to run for longer than a user would ever wait."""
    sdk_attempts = settings.LLM_MAX_RETRIES + 1
    app_attempts = max(CHUNK_ERROR_RETRIES, CHUNK_COUNT_RETRIES) + 1
    worst = settings.LLM_TIMEOUT * sdk_attempts * app_attempts
    assert worst <= 1800, (
        f"worst case per chunk is {worst}s ({worst/60:.0f} min); "
        "keep it under 30 minutes"
    )
