import whisper
from loader import Loader
import time


def main():
    link = input("Please provide YouTube video link: ")
    load = Loader(link)
    title = load.download_audio()

    start_t = time.time()
    model = whisper.load_model("base")
    result = model.transcribe(title)

    if title.endswith(".mp4"):
        title = title.replace(".mp4", ".txt")

    with open(title, "w") as file:
        file.write(result['text'])

    print(f"total time for whisper: {time.time() - start_t}")
    print("Transcription saved")


if __name__ == "__main__":
    main()
