import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, get_db
from app.routers import config_router, upload, transcription, refinement, analysis, translation
from app.metrics import inc, cleanup_runs_total, cleanup_items_deleted_total


async def cleanup_old_files():
    """Periodically delete files and DB records older than CLEANUP_TTL_HOURS."""
    while True:
        await asyncio.sleep(3600)  # Check every hour
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.CLEANUP_TTL_HOURS)
            async with get_db() as db:
                # Get old files to delete from disk
                cursor = await db.execute(
                    "SELECT file_path, mp3_path FROM files WHERE created_at < ?",
                    (cutoff.isoformat(),),
                )
                rows = await cursor.fetchall()
                files_deleted = 0
                for row in rows:
                    for path in [row["file_path"], row["mp3_path"]]:
                        if path and os.path.exists(path):
                            os.unlink(path)
                            files_deleted += 1

                # Delete old DB records (cascade via foreign keys)
                cursor = await db.execute("DELETE FROM analyses WHERE transcription_id IN (SELECT id FROM transcriptions WHERE created_at < ?)", (cutoff.isoformat(),))
                analyses_deleted = cursor.rowcount
                cursor = await db.execute("DELETE FROM speaker_mappings WHERE transcription_id IN (SELECT id FROM transcriptions WHERE created_at < ?)", (cutoff.isoformat(),))
                mappings_deleted = cursor.rowcount
                cursor = await db.execute("DELETE FROM transcriptions WHERE created_at < ?", (cutoff.isoformat(),))
                transcriptions_deleted = cursor.rowcount
                cursor = await db.execute("DELETE FROM files WHERE created_at < ?", (cutoff.isoformat(),))
                db_files_deleted = cursor.rowcount
                await db.commit()

            inc(cleanup_runs_total, "success")
            inc(cleanup_items_deleted_total, "file", amount=files_deleted + db_files_deleted)
            inc(cleanup_items_deleted_total, "transcription", amount=transcriptions_deleted)
            inc(cleanup_items_deleted_total, "analysis", amount=analyses_deleted)
            inc(cleanup_items_deleted_total, "speaker_mapping", amount=mappings_deleted)
        except Exception as e:
            inc(cleanup_runs_total, "failed")
            print(f"Cleanup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.TEMP_PATH, exist_ok=True)
    await init_db(settings.db_path)
    cleanup_task = asyncio.create_task(cleanup_old_files())
    yield
    cleanup_task.cancel()


app = FastAPI(title="Transcription Service", lifespan=lifespan)

if settings.DEV_MODE:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(config_router.router)
app.include_router(upload.router)
app.include_router(transcription.router)
app.include_router(refinement.router)
app.include_router(analysis.router)
app.include_router(translation.router)

# Serve frontend static files (only when built files exist, i.e., in Docker)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve index.html for all non-API routes (SPA client-side routing)."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        # Serve root-level static files (e.g. favicon, logo) if they exist
        candidate = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(static_dir, "index.html"))
