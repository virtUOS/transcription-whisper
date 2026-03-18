from app.config import settings
from app.services.asr.base import ASRBackend

def get_asr_backend() -> ASRBackend:
    if settings.ASR_BACKEND == "whisperx":
        from app.services.asr.whisperx import WhisperXBackend
        return WhisperXBackend()
    else:
        from app.services.asr.murmurai import MurmurAIBackend
        return MurmurAIBackend()
