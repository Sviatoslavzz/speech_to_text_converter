from faster_whisper import WhisperModel
from transcribers.abscract import AbstractTranscriber


class FasterWhisperTranscriber(AbstractTranscriber):

    def __init__(self, model):
        super().__init__(model)

    def transcribe(self, path: str) -> str:
        model = WhisperModel(self.model, device="cpu", compute_type="int8")  # TODO прокинуть настройки через конфиг
        segments, info = model.transcribe(path, beam_size=5)
        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
        result = ""
        for segment in segments:
            result += segment.text

        return result
