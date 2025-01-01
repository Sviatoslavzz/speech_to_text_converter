import pytest
from pydantic import ValidationError
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber
from transcribers.whisper_transcriber import WhisperTranscriber

from config.models import TranscriberConfig


def test_transcriber_config_default():
    conf = TranscriberConfig()
    assert conf.q_size == 300
    assert conf.cls == FasterWhisperTranscriber
    assert conf.model == "small"


def test_transcriber_config():
    data = {
        "q_size": 200,
        "cls": "WhisperTranscriber",
        "model": "medium",
    }
    conf = TranscriberConfig(**data)
    assert conf.q_size == 200
    assert conf.cls == WhisperTranscriber
    assert conf.model == "medium"


def test_transcriber_config_raise():
    data = {
        "q_size": 200,
        "cls": "WrongClass",
        "model": "medium",
    }
    with pytest.raises(ValidationError):
        TranscriberConfig(**data)
