from dataclasses import dataclass, asdict
from loguru import logger

from faster_whisper import WhisperModel
from transcribers.abscract import AbstractTranscriber


class FasterWhisperTranscriber(AbstractTranscriber):
    @dataclass
    class Config:
        model_size_or_path: str
        device: str = "cpu"
        device_index: int | list[int] = 0
        compute_type: str = "default"
        cpu_threads: int = 6
        num_workers: int = 1
        download_root: str | None = None
        local_files_only: bool = False
        files: dict = None

    def __init__(self, model: str, device: str | None = "auto"):
        if not self.validate_model(model):
            logger.error(f"Model {model} is not valid")
            raise ValueError(f"Model {model} is not valid")
        self.config = self.Config(model_size_or_path=model, device=device)
        logger.info(f"FasterWhisperTranscriber init with a model {self.config.model_size_or_path}")

    def transcribe(self, path: str) -> str:
        model = WhisperModel(**asdict(self.config))
        logger.info("FasterWhisperTranscriber transcription started")
        segments, info = model.transcribe(path)
        logger.info(f"Detected language {info.language} with probability {info.language_probability}")
        result = ""
        for segment in segments:
            result += segment.text

        return result
