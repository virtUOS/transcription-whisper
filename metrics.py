"""
Prometheus metrics for the transcription service.
This module defines and manages all metrics collected by the application.
"""

import time
import os
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server

# Application info metric
app_info = Info('transcription_app_info', 'Information about the transcription application')
app_info.info({
    'version': '1.0.0',
    'name': 'transcription-whisper',
    'description': 'Streamlit transcription service using Whisper models'
})

# Core application metrics
page_views_total = Counter(
    'transcription_page_views_total',
    'Total number of page views',
    ['language']
)

# File upload metrics
file_uploads_total = Counter(
    'transcription_file_uploads_total',
    'Total number of file uploads',
    ['file_type', 'status']
)

file_upload_size_bytes = Histogram(
    'transcription_file_upload_size_bytes',
    'Size of uploaded files in bytes',
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600, 1073741824]  # 1KB to 1GB
)

# Transcription metrics
transcriptions_total = Counter(
    'transcription_jobs_total',
    'Total number of transcription jobs',
    ['language', 'model', 'status', 'speakers_detected']
)

transcription_duration_seconds = Histogram(
    'transcription_duration_seconds',
    'Time taken for transcription jobs',
    ['language', 'model'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600]  # 1s to 1h
)

transcription_file_duration_seconds = Histogram(
    'transcription_file_duration_seconds',
    'Duration of audio/video files being transcribed',
    buckets=[10, 30, 60, 300, 600, 1200, 1800, 3600, 7200]  # 10s to 2h
)

# Active sessions and processing
active_sessions = Gauge(
    'transcription_active_sessions',
    'Number of active user sessions'
)

active_transcriptions = Gauge(
    'transcription_active_jobs',
    'Number of currently processing transcription jobs'
)

# Model usage metrics
model_usage_total = Counter(
    'transcription_model_usage_total',
    'Total usage count per Whisper model',
    ['model']
)

# Language usage metrics
language_usage_total = Counter(
    'transcription_language_usage_total',
    'Total usage count per transcription language',
    ['language']
)

# Error metrics
errors_total = Counter(
    'transcription_errors_total',
    'Total number of errors',
    ['error_type', 'component']
)

# User interaction metrics
user_actions_total = Counter(
    'transcription_user_actions_total',
    'Total number of user actions',
    ['action', 'format']
)

# Format download metrics
downloads_total = Counter(
    'transcription_downloads_total',
    'Total number of file downloads',
    ['format']
)

# Speaker detection metrics
speaker_detection_total = Counter(
    'transcription_speaker_detection_total',
    'Total speaker detection usage',
    ['min_speakers', 'max_speakers']
)

# API response time metrics
api_request_duration_seconds = Histogram(
    'transcription_api_request_duration_seconds',
    'Time taken for API requests',
    ['endpoint', 'method', 'status'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)


class MetricsCollector:
    """Centralized metrics collection class."""
    
    def __init__(self):
        self.start_time = time.time()
        # Expose metrics for direct access
        self.active_sessions = active_sessions
        self.active_transcriptions = active_transcriptions
    
    def track_page_view(self, language='unknown'):
        """Track a page view."""
        page_views_total.labels(language=language).inc()
    
    def track_file_upload(self, file_size, file_type, status='success'):
        """Track file upload metrics."""
        file_uploads_total.labels(file_type=file_type, status=status).inc()
        if status == 'success':
            file_upload_size_bytes.observe(file_size)
    
    def track_transcription_start(self, language, model, min_speakers=0, max_speakers=0):
        """Track when a transcription job starts."""
        transcriptions_total.labels(
            language=language, 
            model=model, 
            status='started',
            speakers_detected='yes' if min_speakers > 0 or max_speakers > 0 else 'no'
        ).inc()
        model_usage_total.labels(model=model).inc()
        language_usage_total.labels(language=language).inc()
        
        if min_speakers > 0 or max_speakers > 0:
            speaker_detection_total.labels(
                min_speakers=str(min_speakers),
                max_speakers=str(max_speakers)
            ).inc()
        
        active_transcriptions.inc()
    
    def track_transcription_complete(self, language, model, duration, status='success'):
        """Track when a transcription job completes."""
        transcriptions_total.labels(
            language=language,
            model=model,
            status=status,
            speakers_detected='unknown'
        ).inc()
        
        if status == 'success':
            transcription_duration_seconds.labels(language=language, model=model).observe(duration)
        
        active_transcriptions.dec()
    
    def track_error(self, error_type, component='app'):
        """Track application errors."""
        errors_total.labels(error_type=error_type, component=component).inc()
    
    def track_user_action(self, action, format_type='unknown'):
        """Track user interactions."""
        user_actions_total.labels(action=action, format=format_type).inc()
    
    def track_download(self, format_type):
        """Track file downloads."""
        downloads_total.labels(format=format_type).inc()
    
    def track_api_request(self, endpoint, method, status_code, duration):
        """Track API request metrics."""
        api_request_duration_seconds.labels(
            endpoint=endpoint,
            method=method,
            status=str(status_code)
        ).observe(duration)
    
    def update_active_sessions(self, count):
        """Update the number of active sessions."""
        active_sessions.set(count)


# Global metrics collector instance
metrics = MetricsCollector()


def start_metrics_server(port=8000):
    """Start the Prometheus metrics HTTP server."""
    try:
        start_http_server(port)
        return True
    except OSError as e:
        if e.errno == 98:  # Address already in use
            # Server is already running, which is fine
            return True
        else:
            print(f"Failed to start metrics server on port {port}: {e}")
            return False
    except Exception as e:
        print(f"Failed to start metrics server on port {port}: {e}")
        return False


def get_metrics_enabled():
    """Check if metrics collection is enabled via environment variable."""
    return os.getenv('ENABLE_METRICS', 'true').lower() in ('true', '1', 'yes', 'on')


def get_metrics_port():
    """Get the metrics server port from environment variable."""
    try:
        return int(os.getenv('METRICS_PORT', '8000'))
    except ValueError:
        return 8000