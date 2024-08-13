from dataclasses import dataclass, asdict

from faster_whisper import WhisperModel
from transcribers.abscract import AbstractTranscriber


class FasterWhisperTranscriber(AbstractTranscriber):
    @dataclass
    class Config:
        model_size_or_path: str
        device: str = "auto"
        device_index: int | list[int] = 0
        compute_type: str = "float32"  # default
        cpu_threads: int = 20
        num_workers: int = 1
        download_root: str | None = None
        local_files_only: bool = False
        files: dict = None

    def __init__(self, model: str, device: str | None = "auto"):
        self.validate_model(model)
        self.config = self.Config(model_size_or_path=model, device=device)

    def transcribe(self, path: str) -> str:
        model = WhisperModel(**asdict(self.config))
        segments, info = model.transcribe(path)
        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
        result = ""
        for segment in segments:
            result += segment.text

        return result
