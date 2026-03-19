import aiosqlite
from contextlib import asynccontextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    original_filename TEXT,
    file_path TEXT,
    mp3_path TEXT,
    media_type TEXT,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transcriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    file_id TEXT REFERENCES files(id),
    asr_job_id TEXT,
    asr_backend TEXT,
    status TEXT,
    language TEXT,
    model TEXT,
    min_speakers INTEGER,
    max_speakers INTEGER,
    initial_prompt TEXT,
    hotwords TEXT,
    result_json TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS speaker_mappings (
    transcription_id TEXT REFERENCES transcriptions(id),
    original_label TEXT,
    custom_name TEXT,
    PRIMARY KEY (transcription_id, original_label)
);

CREATE TABLE IF NOT EXISTS summaries (
    transcription_id TEXT PRIMARY KEY REFERENCES transcriptions(id),
    summary_json TEXT,
    llm_provider TEXT,
    llm_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS protocols (
    transcription_id TEXT PRIMARY KEY REFERENCES transcriptions(id),
    protocol_json TEXT,
    llm_provider TEXT,
    llm_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_db_path: str = ""


async def init_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


@asynccontextmanager
async def get_db(db_path: str | None = None):
    path = db_path or _db_path
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        yield db
