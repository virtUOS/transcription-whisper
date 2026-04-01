import uuid

import aiosqlite
from contextlib import asynccontextmanager
from app.config import settings

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_archived INTEGER DEFAULT 0
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
    id TEXT PRIMARY KEY,
    transcription_id TEXT REFERENCES transcriptions(id),
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
    ("expires_at", "files", "expires_at TIMESTAMP"),
    ("is_archived", "files", "is_archived INTEGER DEFAULT 0"),
    ("title", "transcriptions", "title TEXT"),
    ("has_video", "files", "has_video INTEGER"),
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
        # Migrate analyses table: add `id` column as primary key
        cursor = await db.execute("PRAGMA table_info(analyses)")
        analysis_columns = {row[1] for row in await cursor.fetchall()}
        if "id" not in analysis_columns:
            await db.execute("ALTER TABLE analyses RENAME TO _analyses_old")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    transcription_id TEXT REFERENCES transcriptions(id),
                    analysis_json TEXT,
                    template TEXT,
                    custom_prompt TEXT,
                    language TEXT,
                    llm_provider TEXT,
                    llm_model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Clean up orphaned in-progress placeholders
            await db.execute("DELETE FROM _analyses_old WHERE analysis_json IS NULL")
            # Copy existing rows, generating UUIDs in Python
            cursor = await db.execute(
                "SELECT transcription_id, analysis_json, template, custom_prompt, language, llm_provider, llm_model, created_at FROM _analyses_old"
            )
            rows = await cursor.fetchall()
            for row in rows:
                new_id = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO analyses (id, transcription_id, analysis_json, template, custom_prompt, language, llm_provider, llm_model, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (new_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]),
                )
            await db.execute("DROP TABLE _analyses_old")
            await db.commit()

        # Backfill expires_at for existing files
        await db.execute(
            "UPDATE files SET expires_at = datetime(created_at, '+' || ? || ' hours') WHERE expires_at IS NULL",
            (str(settings.DEFAULT_EXPIRY_HOURS),),
        )
        # Normalize any ISO-format (T-separator) timestamps to SQLite format (space-separator)
        await db.execute(
            "UPDATE files SET expires_at = strftime('%Y-%m-%d %H:%M:%S', expires_at) WHERE expires_at LIKE '%T%'"
        )
        await db.commit()


@asynccontextmanager
async def get_db(db_path: str | None = None):
    path = db_path or _db_path
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        yield db
