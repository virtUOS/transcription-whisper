import json
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.dependencies import get_current_user
from app.router_helpers import ensure_transcription_owned, reset_translation_state
from app.models import UserInfo, TranslationRequest, Utterance
from app.database import get_db
from app.services.llm import get_llm_provider
from app.services.llm.prompt import (
    build_translation_system_prompt,
    build_translation_user_prompt,
    chunk_utterances_for_refinement,
)
from app.metrics import inc, measure_llm_operation, track_llm_tokens, deletions_total

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

    from app.services.source_tracking import hash_utterance_texts, select_source

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT status, result_json, refined_utterances_json,
                      translated_utterances_json, translation_language,
                      translation_source, translation_source_hash
               FROM transcriptions WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transcription not found")

        status = row["status"]
        result_json = row["result_json"]
        refined_json = row["refined_utterances_json"]
        translated_json = row["translated_utterances_json"]
        translation_lang = row["translation_language"]
        cached_source = row["translation_source"]
        cached_hash = row["translation_source_hash"]

        if translated_json and translated_json != "" and translation_lang == body.target_language:
            current_source_json = refined_json if cached_source == "refined" else result_json
            source_available = bool(current_source_json) and current_source_json != ""
            current_hash = (
                hash_utterance_texts(json.loads(current_source_json))
                if source_available else None
            )
            stale = bool(cached_hash) and current_hash is not None and current_hash != cached_hash
            return {
                "utterances": json.loads(translated_json),
                "language": translation_lang,
                "source": cached_source or "original",
                "source_hash": cached_hash,
                "stale": stale,
                "source_available": source_available,
            }

        if translated_json == "":
            raise HTTPException(status_code=429, detail="Translation already in progress")

        if status != "completed":
            raise HTTPException(status_code=400, detail="Transcription not completed")

        try:
            chosen_source = select_source(
                explicit=body.source,
                result_json=result_json,
                refined_json=refined_json,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        source_json = refined_json if chosen_source == "refined" else result_json
        source_utterances = json.loads(source_json or "[]")
        source_hash = hash_utterance_texts(source_utterances)

        await db.execute(
            "UPDATE transcriptions SET translated_utterances_json = '', translation_language = ? "
            "WHERE id = ? AND user_id = ?",
            (body.target_language, transcription_id, user.id),
        )
        await db.commit()

    try:
        async with measure_llm_operation("translation"):
            translated = await _call_llm_translation(provider, source_utterances, body.target_language)
    except HTTPException:
        raise
    except Exception:
        await reset_translation_state(transcription_id, user.id)
        raise HTTPException(status_code=500, detail="Translation failed")

    if len(translated) != len(source_utterances):
        await reset_translation_state(transcription_id, user.id)
        raise HTTPException(
            status_code=500,
            detail=f"LLM returned {len(translated)} utterances, expected {len(source_utterances)}",
        )

    translated_json_str = json.dumps(translated, ensure_ascii=False)

    async with get_db() as db:
        await db.execute(
            """UPDATE transcriptions
                 SET translated_utterances_json = ?,
                     translation_language = ?,
                     translation_source = ?,
                     translation_source_hash = ?
               WHERE id = ? AND user_id = ?""",
            (translated_json_str, body.target_language, chosen_source, source_hash,
             transcription_id, user.id),
        )
        await db.commit()

    return {
        "utterances": translated,
        "language": body.target_language,
        "source": chosen_source,
        "source_hash": source_hash,
        "stale": False,
        "source_available": True,
    }


@router.get("/api/translate/{transcription_id}")
async def get_translation(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    from app.services.source_tracking import hash_utterance_texts

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT translated_utterances_json, translation_language,
                      translation_source, translation_source_hash,
                      result_json, refined_utterances_json
               FROM transcriptions WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Transcription not found")

    translated_json = row["translated_utterances_json"]
    if not translated_json or translated_json == "":
        raise HTTPException(status_code=404, detail="No translation found")

    source = row["translation_source"] or "original"
    cached_hash = row["translation_source_hash"]
    current_source_json = row["refined_utterances_json"] if source == "refined" else row["result_json"]
    source_available = bool(current_source_json) and current_source_json != ""
    current_hash = (
        hash_utterance_texts(json.loads(current_source_json))
        if source_available else None
    )
    stale = bool(cached_hash) and current_hash is not None and current_hash != cached_hash

    return {
        "utterances": json.loads(translated_json),
        "language": row["translation_language"],
        "source": source,
        "source_hash": cached_hash,
        "stale": stale,
        "source_available": source_available,
    }


@router.delete("/api/translate/{transcription_id}")
async def delete_translation(
    transcription_id: str,
    user: UserInfo = Depends(get_current_user),
):
    async with get_db() as db:
        await ensure_transcription_owned(db, transcription_id, user.id)

        await db.execute(
            """UPDATE transcriptions
               SET translated_utterances_json = NULL,
                   translation_language = NULL,
                   translation_source = NULL,
                   translation_source_hash = NULL
               WHERE id = ? AND user_id = ?""",
            (transcription_id, user.id),
        )
        await db.commit()

    inc(deletions_total, "translation")
    return {"status": "deleted"}
