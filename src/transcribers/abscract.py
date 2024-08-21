from abc import ABC, abstractmethod


class AbstractTranscriber(ABC):

    @staticmethod
    def validate_model(model):
        if model not in [
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
        ]:
            raise ValueError(f"Model {model} is not valid")

    @abstractmethod
    def transcribe(self, path: str) -> str:
        pass

    # @abstractmethod
    # def _save_to_file(self, path: str, transcription: str) -> None:
    #     pass
