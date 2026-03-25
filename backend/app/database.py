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
    completed_at TIMESTAMP,
    refined_utterances_json TEXT,
    refinement_metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS speaker_mappings (
    transcription_id TEXT REFERENCES transcriptions(id),
    original_label TEXT,
    custom_name TEXT,
    PRIMARY KEY (transcription_id, original_label)
);

CREATE TABLE IF NOT EXISTS analyses (
    transcription_id TEXT PRIMARY KEY REFERENCES transcriptions(id),
    analysis_json TEXT,
    template TEXT,
    custom_prompt TEXT,
    language TEXT,
    llm_provider TEXT,
    llm_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_db_path: str = ""


MIGRATIONS = [
    # (column_name, table, column_def)
    ("refined_utterances_json", "transcriptions", "refined_utterances_json TEXT"),
    ("refinement_metadata_json", "transcriptions", "refinement_metadata_json TEXT"),
    ("translated_utterances_json", "transcriptions", "translated_utterances_json TEXT"),
    ("translation_language", "transcriptions", "translation_language TEXT"),
]


async def init_db(db_path: str) -> None:
    global _db_path
    _db_path = db_path
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        # Add columns that may be missing on existing databases
        for col_name, table, col_def in MIGRATIONS:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            columns = {row[1] for row in await cursor.fetchall()}
            if col_name not in columns:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        await db.commit()


@asynccontextmanager
async def get_db(db_path: str | None = None):
    path = db_path or _db_path
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        yield db
