from abc import ABC, abstractmethod


class AbstractTranscriber(ABC):

    def __init__(self, model):  # TODO заменить на конфигурационный файл
        self.model = model  # TODO валидация модели (список существующих)

    @abstractmethod
    def transcribe(self, path: str) -> str:
        pass

    # @abstractmethod
    # def _save_to_file(self, path: str, transcription: str) -> None:
    #     pass


"""
tiny, tiny.en, base, base.en,
small, small.en, distil-small.en, medium, medium.en, distil-medium.en, large-v1,
large-v2, large-v3, large, distil-large-v2 or distil-large-v3
"""
