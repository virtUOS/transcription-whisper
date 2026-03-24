import pytest
from app.services.asr.base import ASRBackend

def test_asr_backend_is_abstract():
    with pytest.raises(TypeError):
        ASRBackend()
