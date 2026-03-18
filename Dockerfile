# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + static files
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./static
USER nobody
EXPOSE 8000
HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
