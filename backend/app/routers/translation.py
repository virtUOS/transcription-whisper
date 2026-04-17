import json
import time
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.dependencies import get_current_user
from app.models import UserInfo, TranslationRequest, Utterance
from app.database import get_db
from app.services.llm import get_llm_provider
from app.services.llm.prompt import (
    build_translation_system_prompt,
    build_translation_user_prompt,
    chunk_utterances_for_refinement,
)
from app.metrics import inc, observe, track_llm_tokens, llm_requests_total, llm_duration_seconds, llm_errors_total, deletions_total, errors_total

router = APIRouter()


async def _call_llm_translation(provider, utterances: list[dict], target_language: str) -> list[dict]:
    """Call LLM to translate utterances, chunking if needed."""
    chunks = chunk_utterances_for_refinement(utterances)
    all_translated: list[dict] = []

    for chunk in chunks:
        system = build_translation_system_prompt(target_language)
        user = build_translation_user_prompt(chunk)

        # Use provider's internal chat method depending on type
        from app.services.llm.openai import OpenAIProvider
        from app.services.llm.ollama import OllamaProvider

        if isinstance(provider, OpenAIProvider):
            resp = await provider._client.chat.completions.create(
                model=provider._model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            track_llm_tokens(settings.LLM_PROVIDER, provider._model, "translation", getattr(resp, "usage", None))
            data = json.loads(resp.choices[0].message.content or "{}")
        elif isinstance(provider, OllamaProvider):
            content = await provider._chat(system, user, operation="translation")
            data = json.loads(content)
        else:
            raise HTTPException(status_code=503, detail="Unsupported LLM provider for translation")

        all_translated.extend(data.get("utterances", []))

    return all_translated


@router.post("/api/translate/{transcription_id}")
async def translate_transcription(
    transcription_id: str,
    body: TranslationRequest,
    user: UserInfo = Depends(get_current_user),
):
    provider = get_llm_provider()
    if not provider:
        raise HTTPException(status_code=503, detail="LLM provider not configured")

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT status, result_json, translated_utterances_json, translation_language
               FROM transcriptions WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        status, result_json, translated_json, translation_lang = row

        # Return cached translation if same language
        if translated_json and translated_json != "" and translation_lang == body.target_language:
            return {
                "utterances": json.loads(translated_json),
                "language": translation_lang,
            }

        # Check if translation is already in progress (empty string sentinel)
        if translated_json == "":
            raise HTTPException(status_code=429, detail="Translation already in progress")

        if status != "completed":
            raise HTTPException(status_code=400, detail="Transcription not completed")

        original_utterances = json.loads(result_json or "[]")

        # Set in-progress sentinel
        await db.execute(
            "UPDATE transcriptions SET translated_utterances_json = '', translation_language = ? WHERE id = ? AND user_id = ?",
            (body.target_language, transcription_id, user.id),
        )
        await db.commit()

    start_time = time.monotonic()
    try:
        translated = await _call_llm_translation(provider, original_utterances, body.target_language)
    except HTTPException:
        raise
    except Exception:
        inc(llm_errors_total, settings.LLM_PROVIDER, settings.LLM_MODEL, "translation")
        inc(errors_total, "llm_failed", "translation")
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET translated_utterances_json = NULL, translation_language = NULL WHERE id = ? AND user_id = ?",
                (transcription_id, user.id),
            )
            await db.commit()
        raise HTTPException(status_code=500, detail="Translation failed")

    duration = time.monotonic() - start_time
    inc(llm_requests_total, settings.LLM_PROVIDER, settings.LLM_MODEL, "translation")
    observe(llm_duration_seconds, duration, settings.LLM_PROVIDER, settings.LLM_MODEL, "translation")

    if len(translated) != len(original_utterances):
        async with get_db() as db:
            await db.execute(
                "UPDATE transcriptions SET translated_utterances_json = NULL, translation_language = NULL WHERE id = ? AND user_id = ?",
                (transcription_id, user.id),
            )
            await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"LLM returned {len(translated)} utterances, expected {len(original_utterances)}",
        )

    translated_json_str = json.dumps(translated, ensure_ascii=False)

    async with get_db() as db:
        await db.execute(
            """UPDATE transcriptions
               SET translated_utterances_json = ?, translation_language = ?
               WHERE id = ? AND user_id = ?""",
            (translated_json_str, body.target_language, transcription_id, user.id),
        )
        await db.commit()

    return {
        "utterances": translated,
        "language": body.target_language,
    }


@router.get("/api/translate/{transcription_id}")
async def get_translation(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT translated_utterances_json, translation_language
               FROM transcriptions WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Transcription not found")

    translated_json, translation_lang = row["translated_utterances_json"], row["translation_language"]

    if not translated_json or translated_json == "":
        raise HTTPException(status_code=404, detail="No translation found")

    return {
        "utterances": json.loads(translated_json),
        "language": translation_lang,
    }


@router.delete("/api/translate/{transcription_id}")
async def delete_translation(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM transcriptions WHERE id = ? AND user_id = ?",
            (transcription_id, user.id),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Transcription not found")

        await db.execute(
            """UPDATE transcriptions
               SET translated_utterances_json = NULL, translation_language = NULL
               WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        await db.commit()

    inc(deletions_total, "translation")
    return {"status": "deleted"}
