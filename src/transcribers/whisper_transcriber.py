import warnings
from pathlib import Path

import whisper
from loguru import logger

from transcribers.abscract import AbstractTranscriber

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


class WhisperTranscriber(AbstractTranscriber):
    WHISPER_FORMATS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "mov"]  # TODO take from config

    def __init__(self, model: str):
        if not self.validate_model(model):
            logger.error(f"Model {model} is not valid")
            raise ValueError

        self.model = model
        logger.info(f"WhisperTranscriber init with a model {self.model}")

    def transcribe(self, path: Path) -> str:
        if path.suffix.lstrip(".") not in self.WHISPER_FORMATS:
            logger.error(f"File format is not supported: {path.suffix}")
            raise NotImplementedError("File format is not supported")

        model = whisper.load_model(self.model)
        logger.info("WhisperTranscriber transcription started")
        result = model.transcribe(path.__fspath__())

        return result["text"]
