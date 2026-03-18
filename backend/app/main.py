import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import config_router, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.TEMP_PATH, exist_ok=True)
    await init_db(settings.db_path)
    yield


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
