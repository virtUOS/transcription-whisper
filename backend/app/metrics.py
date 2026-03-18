from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

CONTENT_TYPE = CONTENT_TYPE_LATEST

app_info = Info("transcription_app_info", "Application info")
app_info.info({"version": "1.0.0", "name": "transcription-whisper"})

page_views_total = Counter("transcription_page_views_total", "Total page views", ["language"])
file_uploads_total = Counter("transcription_file_uploads_total", "Total file uploads", ["file_type", "status"])
file_upload_size_bytes = Histogram(
    "transcription_file_upload_size_bytes", "Upload size in bytes",
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600, 1073741824],
)
transcriptions_total = Counter(
    "transcription_jobs_total", "Total transcription jobs",
    ["language", "model", "status", "speakers_detected"],
)
transcription_duration_seconds = Histogram(
    "transcription_duration_seconds", "Transcription duration",
    ["language", "model"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600],
)
active_sessions = Gauge("transcription_active_sessions", "Active sessions")
active_transcriptions = Gauge("transcription_active_jobs", "Active transcription jobs")
model_usage_total = Counter("transcription_model_usage_total", "Model usage", ["model"])
language_usage_total = Counter("transcription_language_usage_total", "Language usage", ["language"])
errors_total = Counter("transcription_errors_total", "Errors", ["error_type", "component"])
user_actions_total = Counter("transcription_user_actions_total", "User actions", ["action", "format"])
downloads_total = Counter("transcription_downloads_total", "Downloads", ["format"])
speaker_renames_total = Counter("transcription_speaker_renames_total", "Speaker renames")
api_request_duration_seconds = Histogram(
    "transcription_api_request_duration_seconds", "API request duration",
    ["endpoint", "method", "status"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)
summary_requests_total = Counter("transcription_summary_requests_total", "Summary requests", ["provider"])
summary_duration_seconds = Histogram(
    "transcription_summary_duration_seconds", "Summary generation duration",
    buckets=[1, 5, 10, 30, 60, 120],
)
asr_backend_requests_total = Counter("transcription_asr_backend_requests_total", "ASR backend requests", ["backend"])


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE)
