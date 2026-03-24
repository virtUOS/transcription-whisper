from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from app.config import settings

CONTENT_TYPE = CONTENT_TYPE_LATEST

_enabled = settings.ENABLE_METRICS


def _counter(name, desc, labels=None):
    if not _enabled:
        return None
    return Counter(name, desc, labels or [])


def _histogram(name, desc, labels=None, buckets=None):
    if not _enabled:
        return None
    kwargs = {}
    if labels:
        kwargs["labelnames"] = labels
    if buckets:
        kwargs["buckets"] = buckets
    return Histogram(name, desc, **kwargs)


def _gauge(name, desc):
    if not _enabled:
        return None
    return Gauge(name, desc)


# --- App info ---
if _enabled:
    app_info = Info("transcription_app_info", "Application info")
    app_info.info({"version": "1.0.0", "name": "transcription-whisper"})

# --- Uploads ---
file_uploads_total = _counter("transcription_file_uploads_total", "Total file uploads", ["file_type", "status"])
file_upload_size_bytes = _histogram(
    "transcription_file_upload_size_bytes", "Upload size in bytes",
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600, 1073741824],
)
file_renames_total = _counter("transcription_file_renames_total", "Total file renames")

# --- Transcription jobs ---
transcriptions_total = _counter(
    "transcription_jobs_total", "Total transcription jobs",
    ["language", "model", "status"],
)
transcription_duration_seconds = _histogram(
    "transcription_duration_seconds", "Transcription duration",
    labels=["language", "model"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600],
)
active_transcriptions = _gauge("transcription_active_jobs", "Active transcription jobs")
diarization_speakers_detected = _histogram(
    "transcription_diarization_speakers_detected", "Number of speakers detected per job",
    buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
)

# --- Editing ---
edits_saved_total = _counter("transcription_edits_saved_total", "Transcription edits saved")
speaker_renames_total = _counter("transcription_speaker_renames_total", "Speaker renames")

# --- Exports / Downloads ---
downloads_total = _counter("transcription_downloads_total", "Downloads", ["format"])

# --- Deletions ---
deletions_total = _counter("transcription_deletions_total", "Resource deletions", ["resource_type"])

# --- LLM (summaries + protocols) ---
llm_requests_total = _counter(
    "transcription_llm_requests_total", "LLM requests",
    ["provider", "model", "operation"],
)
llm_duration_seconds = _histogram(
    "transcription_llm_duration_seconds", "LLM request duration",
    labels=["provider", "model", "operation"],
    buckets=[1, 5, 10, 30, 60, 120],
)
llm_errors_total = _counter(
    "transcription_llm_errors_total", "LLM errors",
    ["provider", "model", "operation"],
)

# --- Errors ---
errors_total = _counter("transcription_errors_total", "Errors", ["error_type", "component"])

# --- API request duration ---
api_request_duration_seconds = _histogram(
    "transcription_api_request_duration_seconds", "API request duration",
    labels=["endpoint", "method", "status"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

# --- WebSocket ---
websocket_connections_active = _gauge("transcription_websocket_connections_active", "Active WebSocket connections")
websocket_connections_total = _counter("transcription_websocket_connections_total", "Total WebSocket connections")

# --- Cleanup ---
cleanup_runs_total = _counter("transcription_cleanup_runs_total", "Cleanup job runs", ["status"])
cleanup_items_deleted_total = _counter("transcription_cleanup_items_deleted_total", "Items deleted by cleanup", ["resource_type"])


# --- Helper for safe instrumentation ---
def inc(counter, *args, amount=1):
    """Safely increment a counter (no-op if metrics disabled)."""
    if counter is None:
        return
    if args:
        counter.labels(*args).inc(amount)
    else:
        counter.inc(amount)


def observe(histogram, value, *args):
    """Safely observe a histogram value (no-op if metrics disabled)."""
    if histogram is None:
        return
    if args:
        histogram.labels(*args).observe(value)
    else:
        histogram.observe(value)


def gauge_inc(gauge, amount=1):
    """Safely increment a gauge (no-op if metrics disabled)."""
    if gauge is not None:
        gauge.inc(amount)


def gauge_dec(gauge, amount=1):
    """Safely decrement a gauge (no-op if metrics disabled)."""
    if gauge is not None:
        gauge.dec(amount)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE)
