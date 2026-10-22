# Project: Transcription Whisper

Instructions for coding agents working in this repository.

## Quick Reference

- **Frontend**: React 19 + TypeScript, Vite 8, Zustand, Tailwind CSS 4
- **Backend**: FastAPI (Python 3.12), async SQLite, Uvicorn
- **Deployment**: Multi-stage Docker build, Caddy reverse proxy

## Commands

### Frontend
```bash
cd frontend
npm install          # install dependencies
npm run dev          # dev server on :5173
npm run build        # production build (runs `tsc -b` first, so it also type-checks)
npm run typecheck    # type-check only (`tsc -b`)
npm run lint         # eslint
npm test             # vitest, single run
npm run test:watch   # vitest in watch mode
```

Do **not** use `npx tsc --noEmit` here — the root `tsconfig.json` is solution-style
(`"files": []` plus project references), so that command silently checks nothing and
exits 0 even with type errors in `src/`. Use `npm run typecheck`.

### Backend
```bash
cd backend
pip install -r requirements-dev.txt   # runtime + test deps
uvicorn app.main:app --reload --port 8000
pytest               # run tests
```

Dependencies are pinned with hashes. Edit `requirements.in` (runtime) or
`requirements-dev.in` (test-only), never the generated `requirements*.txt`, then
regenerate both lock files with the `uv pip compile` commands in the header of
`requirements.in`. The Docker image installs only `requirements.txt`, with
`--require-hashes`, so test packages never reach production.

### Docker
```bash
docker build -t transcription-app .
docker run -p 8000:8000 --env-file .env transcription-app

# Subpath deployment (e.g., /test/)
docker build --build-arg VITE_BASE_PATH=/test -t transcription-test .
```

## Architecture

- Frontend SPA served as static files by FastAPI, view-based navigation (archive/upload/record/detail/presets/settings)
- API routes under `/api/*`, WebSocket at `/api/ws/status/{id}`
- Pluggable ASR backends: MurmurAI or WhisperX — both are remote HTTP API servers the app calls out to (see README §"ASR Configuration" for the server projects). The admin picks one at deploy time via the `ASR_BACKEND` env var; the choice is not user-facing and there is no UI control to switch backends. `ASRBackend.cleanup(job_id)` is a best-effort hook (no-op by default) that `_run_transcription` calls after the result is stored, and after a failure when a job id exists; MurmurAI implements it as `DELETE /v1/transcript/{id}` because the server otherwise keeps every transcript forever. It must never raise — failures log a warning and count `errors_total{error_type="asr_cleanup_failed"}`.
- Pluggable LLM providers: OpenAI-compatible API (OpenAI, vLLM, etc.) or Ollama — for analysis, translation, and transcription refinement
- Database: async SQLite with foreign keys enabled
- All frontend API calls go through centralized client at `frontend/src/api/client.ts`
- Base path for subpath deployments configured via `VITE_BASE_PATH` env var at build time
- Two authentication paths share one dependency (`get_current_user`): reverse-proxy headers (`X-Auth-Request-User/Email`) for the browser, and `Authorization: Bearer tw_…` for personal API tokens when `ENABLE_API_TOKENS=true`. Token path wins when present; invalid tokens return 401 without header fallback. Tokens are sha256-hashed in `api_tokens`, surfaced via `/api/tokens` (router mounted only when flag is on; OpenAPI hidden when off) and a Settings view. WS (`/api/ws/status/{id}`) accepts `?token=tw_…` since browsers cannot set custom WS headers

## Code Style

- Frontend: ESLint 9 + TypeScript ESLint, no semicolons enforced by formatter
- Backend: Standard Python conventions, async/await throughout
- Commit messages: conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- Never add "Co-Authored-By" lines to commit messages

## Key Directories

- `frontend/src/api/` — API client and types
- `frontend/src/components/` — React components (SubtitleEditor, AnalysisView, SpeakerMapping, FormatViewer, HelpDrawer, etc.)
- `frontend/src/help/` — Help drawer markdown content (en/, de/) and SVG diagram assets (assets/)
- `frontend/src/i18n/` — Internationalization locale files (en.json, de.json)
- `frontend/src/utils/` — Utility functions (formatting, downloads)
- `frontend/src/store/index.ts` — Zustand state management
- `frontend/src/hooks/` — Custom React hooks (e.g. useBeforeUnloadWarning)
- `backend/app/routers/` — FastAPI route handlers (upload, transcription, analysis, translation, refinement, presets, config_router, tokens)
- `backend/app/services/api_tokens.py` — API-token service helpers (create/list/revoke/resolve/cleanup). `resolve_token` returns `(UserInfo, token_id) | None`. `cleanup_stale_tokens` is invoked from the existing `cleanup_old_files` loop in `main.py`; do not start a second scheduler
- `backend/app/services/asr/` — ASR backend implementations
- `backend/app/services/llm/` — LLM provider implementations and prompt templates
- `backend/app/models.py` — Pydantic request/response models
- `backend/app/dependencies.py` — Authentication/authorization dependencies
- `backend/app/database.py` — SQLite schema and connection management
- `backend/app/config.py` — Environment variable configuration
- `backend/app/metrics.py` — Prometheus metrics definitions and instrumentation helpers (`inc`, `observe`, `gauge_inc/dec/set`, `track_llm_tokens`)

## Observability

- Metrics are exposed at `/metrics` when `ENABLE_METRICS=true`. Use the safe helpers in `metrics.py` rather than calling `Counter/Gauge/Histogram` directly — they no-op when metrics are disabled.
- Transcription flow emits: `queue_depth` / `queue_wait_seconds` (submission → processing), `audio_duration_seconds` (via `ffprobe`), `duration_seconds` and `realtime_factor` (on completion). All carry a `backend` label (`murmurai`/`whisperx`); `jobs_total` and `duration_seconds` were updated to include it.
- Diarization speaker counts are tracked as `diarization_speakers_total{count="N"}` — a Counter labelled by exact speaker count, capped at 20 (the product limit). Not a histogram: speaker count is a bounded small-integer category, so per-value counters give exact, directly-readable counts in dashboards. Increment via `inc(diarization_speakers_total, str(min(n, 20)))`.
- LLM providers (`openai.py`, `ollama.py`) call `track_llm_tokens(provider, model, operation, usage)` inside their shared chat helpers. New LLM calls added outside these helpers (e.g. a direct `_call_llm` path) must call it too — pass the matching `operation` label (`analysis`, `translation`, `refinement`, `title`).
- Storage usage gauge is refreshed at startup and after each cleanup run in `main.py` — no separate task.
- WebSocket handler tracks message counts and disconnect reasons; auth failures are counted in `dependencies.py` and the WS handler.
- API-token auth emits `api_token_auth_total{result}` on both HTTP and WS paths; `api_tokens_created_total` / `api_tokens_revoked_total` wrap the management endpoints; `api_tokens_active` gauge is refreshed at startup and inside `cleanup_old_files`. `auth_failures_total{reason}` gained `invalid_token` — expired/revoked tokens are merged into that bucket (service returns `None` uniformly).
