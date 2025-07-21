# Transcription Service App

[Transcription Service App](https://pvm002.virtuos.uni-osnabrueck.de/) is a web app for universities to make simple transcriptions from video or audio files in multiple languages, currently tailored towards Open AI's Whisper models.

![screenshot.png](docs/assets/screenshot.png)

Some of its features are:
- Supports transcriptions with or without simultaneous translations to multiple languages.
- Simple interface.
- Configurable access to Open AI's Whisper models (tiny, base, small, medium, large-v1, large-v2, large-v3, large-v3-turbo).
- Supports upload from videos and audio files (up to 1gb).
- Users can edit and download transcription results in 4 different formats (txt, vtt, srt and json).
- Diarization support to detect multiple speakers (up to 20).
- Srt, vtt and json formats provide timestamp and speaker information (when available).
- Transcribed subtitles can be activated in uploaded videos.

# Usage & Configuration

You first need to set up a [whisperx API server](https://github.com/virtUOS/whisperx-api) to work with this app.

Some environment variables should be set. Here is an example of a .env file:

```yml
# PATH to the ffmpeg library in your system
FFMPEG_PATH=/usr/bin/ffmpeg
# Path where temporal files will be generated
TEMP_PATH=transcription-whisper-temp
# Uncomment this up if you're using an authentication process to allow users to log out
#LOGOUT_URL=/oauth2/sign_out
# Url and port to the API server
API_URL=http://111.111.111.11:11300
# Available Whisper models (comma-separated)
WHISPER_MODELS=tiny,base,small,medium,large-v1,large-v2,large-v3,large-v3-turbo
# Default model selection
DEFAULT_WHISPER_MODEL=base

# Prometheus metrics configuration
ENABLE_METRICS=true
METRICS_PORT=8000
```

## Prometheus Metrics

The application includes comprehensive Prometheus metrics for monitoring usage and performance. When enabled, metrics are exposed on a separate HTTP endpoint for Prometheus to scrape.

### Available Metrics

- **Application Metrics**:
  - `transcription_page_views_total` - Total page views by UI language
  - `transcription_active_sessions` - Number of active user sessions
  - `transcription_app_info` - Application version and metadata

- **File Upload Metrics**:
  - `transcription_file_uploads_total` - Total file uploads by type and status
  - `transcription_file_upload_size_bytes` - File upload size distribution

- **Transcription Metrics**:
  - `transcription_jobs_total` - Total transcription jobs by language, model, and status
  - `transcription_duration_seconds` - Transcription processing time distribution
  - `transcription_active_jobs` - Number of currently processing jobs
  - `transcription_model_usage_total` - Usage count per Whisper model
  - `transcription_language_usage_total` - Usage count per transcription language
  - `transcription_speaker_detection_total` - Speaker detection usage statistics

- **User Interaction Metrics**:
  - `transcription_user_actions_total` - User actions (save, edit) by format
  - `transcription_downloads_total` - File downloads by format

- **API and Error Metrics**:
  - `transcription_api_request_duration_seconds` - API request latency
  - `transcription_errors_total` - Error count by type and component

### Configuration

Metrics are controlled by environment variables:

- `ENABLE_METRICS=true` - Enable/disable metrics collection (default: true)
- `METRICS_PORT=8000` - Port for metrics HTTP server (default: 8000)

### Prometheus Configuration

Add this job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'transcription-app'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
    metrics_path: /metrics
```

### Grafana Dashboard

The metrics are designed to work well with Grafana. Key dashboard panels might include:

- Active sessions and transcription jobs over time
- Transcription success/failure rates
- Processing time percentiles by model
- File upload volume and sizes
- Language and model usage distribution
- Error rates and types

### Testing Metrics

You can test the metrics functionality using the included test script:

```bash
python test_metrics.py
```

## Development

The app is developed in the [streamlit](https://streamlit.io/) framework.

You can install the requirements needed to run and develop the app using `pip install -r requirements.txt`.
Then simply run a development server like this:

```bash
streamlit run app.py
```

The metrics endpoint will be available at `http://localhost:8000/metrics` when the app is running.

## Authors

virtUOS
