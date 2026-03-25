from app.config import settings
from app.services.asr.base import ASRBackend

def get_asr_backend() -> ASRBackend:
    if settings.ASR_BACKEND == "whisperx":
        from app.services.asr.whisperx import WhisperXBackend
        return WhisperXBackend()
    elif settings.ASR_BACKEND == "whisperlivekit":
        from app.services.asr.whisperlivekit import WhisperLiveKitBackend
        return WhisperLiveKitBackend()
    else:
        from app.services.asr.murmurai import MurmurAIBackend
        return MurmurAIBackend()
