import whisper
from yt_dlp_loader import Yt_loader


class Transcriber:

    def __init__(self):
        self._model = whisper.load_model("base")

    def transcribe(self, directory_: str, link: str):
        loader = Yt_loader(link)
        title, is_loaded = loader.download_audio()
        if is_loaded:
            result = self._model.transcribe(title)
            print(f"Transcribing started {title}")
            if title.endswith(".mp3"):
                title = title.replace(".mp3", ".txt")
                with open(f'{directory_}/{title}', "w") as file:
                    file.write(result['text'])
                print(f"Transcription saved\ntitle: {title}\n")
            else:
                print("Please check audio extension")
