from dataclasses import asdict, dataclass
from pathlib import Path

from faster_whisper import WhisperModel
from loguru import logger

from transcribers.abscract import AbstractTranscriber


class FasterWhisperTranscriber(AbstractTranscriber):
    FASTER_WHISPER_FORMATS = ["mp3", "mp4", "m4a", "wav", "webm", "mov", "ogg", "opus"]

    @dataclass
    class Config:
        model_size_or_path: str
        device: str = "cpu"
        device_index: int | list[int] = 0
        compute_type: str = "default"
        cpu_threads: int = 8
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

    def transcribe(self, path: Path) -> str:
        if path.suffix.lstrip(".") not in self.FASTER_WHISPER_FORMATS:
            logger.error(f"File format is not supported: {path.suffix}")
            raise NotImplementedError
        model = WhisperModel(**asdict(self.config))
        logger.info("FasterWhisperTranscriber transcription started")
        segments, info = model.transcribe(path.__fspath__())
        logger.info(f"Detected language {info.language} with probability {info.language_probability}")
        result = ""
        for segment in segments:
            result += segment.text  # TODO а что если сразу в файл писать а не в оперативу?

        return result
