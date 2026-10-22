import json
import os
import shutil

import aiosqlite
import pytest
import pytest_asyncio

from scripts.seed_help_demo import seed

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg not installed; media generation skipped"
)


@pytest_asyncio.fixture
async def seeded(tmp_path):
    db_path = str(tmp_path / "demo.db")
    media_dir = str(tmp_path / "media")
    ids = await seed(db_path, media_dir, make_media=False)
    return db_path, media_dir, ids


async def _rows(db_path, sql, params=()):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(sql, params)
        return await cur.fetchall()


@pytest.mark.asyncio
async def test_seed_creates_completed_transcriptions(seeded):
    db_path, _, ids = seeded
    assert set(ids) == {"transcription_de", "transcription_en", "file_de", "file_en"}
    rows = await _rows(
        db_path, "SELECT * FROM transcriptions WHERE user_id = 'dev-user' AND status = 'completed'"
    )
    assert len(rows) == 2
    for r in rows:
        utterances = json.loads(r["result_json"])
        assert {u["speaker"] for u in utterances} == {"SPEAKER_00", "SPEAKER_01"}
        assert utterances[-1]["end"] > 100_000
        assert r["refined_utterances_json"] and r["refinement_metadata_json"]
        assert r["translated_utterances_json"] and r["translation_language"]


@needs_ffmpeg
@pytest.mark.asyncio
async def test_seed_generates_media(tmp_path):
    db_path = str(tmp_path / "demo.db")
    await seed(db_path, str(tmp_path / "media"))
    files = await _rows(db_path, "SELECT * FROM files")
    assert len(files) == 2
    for f in files:
        assert os.path.exists(f["file_path"]) and os.path.exists(f["mp3_path"])


@pytest.mark.asyncio
async def test_seed_creates_names_analysis_presets_token(seeded):
    db_path, _, ids = seeded
    maps = await _rows(
        db_path, "SELECT * FROM speaker_mappings WHERE transcription_id = ?", (ids["transcription_de"],)
    )
    assert {m["original_label"] for m in maps} == {"SPEAKER_00", "SPEAKER_01"}
    analyses = await _rows(db_path, "SELECT * FROM analyses WHERE analysis_json IS NOT NULL")
    assert len(analyses) == 2
    assert "summary" in json.loads(analyses[0]["analysis_json"])
    assert len(await _rows(db_path, "SELECT * FROM transcription_presets")) == 1
    assert len(await _rows(db_path, "SELECT * FROM preset_bundles")) == 1
    assert len(await _rows(db_path, "SELECT * FROM api_tokens WHERE user_id = 'dev-user'")) == 1


@pytest.mark.asyncio
async def test_seed_is_deterministic(tmp_path):
    a = await seed(str(tmp_path / "a.db"), str(tmp_path / "ma"), make_media=False)
    b = await seed(str(tmp_path / "b.db"), str(tmp_path / "mb"), make_media=False)
    assert a == b
