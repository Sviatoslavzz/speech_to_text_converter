import warnings

import whisper
from transcribers.abscract import AbstractTranscriber

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


class WhisperTranscriber(AbstractTranscriber):

    def __init__(self, model):
        self.validate_model(model)
        self.model = model

    def transcribe(self, path: str) -> str:
        model = whisper.load_model(self.model)
        result = model.transcribe(path)

        return result['text']

    # def _save_to_file(self, path: str, transcription: str) -> None:
    #     if path.endswith((".mp3", ".mp4")):
    #         path = path.replace(".mp3", ".txt").replace(".mp4", ".txt")
    #     with open(path, "w") as file:
    #         file.write(transcription)
