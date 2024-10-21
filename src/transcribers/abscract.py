from abc import ABC, abstractmethod
from pathlib import Path


class AbstractTranscriber(ABC):
    @staticmethod
    def validate_model(model: str) -> bool:
        return model in [
            "tiny",
            "tiny.en",
            "base",
            "base.en",
            "small",
            "small.en",
            "distil-small.en",
            "medium",
            "medium.en",
            "distil-medium.en",
            "large-v1",
            "large-v2",
            "large-v3",
            "large",
            "distil-large-v2",
            "distil-large-v3",
        ]

    @abstractmethod
    def transcribe(self, path: Path) -> str:
        pass

    @abstractmethod
    def __repr__(self):
        pass
