import whisper
from loader import Loader
import time
import warnings

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


def collect_links() -> list:
    links = []
    print("Please provide YouTube video links each on new line then write done:")
    links.append(input())
    link = input()
    while link != "done":
        links.append(link)
        link = input()
    return links


def main():
    links = collect_links()
    print("starting loop...")
    for i, link in enumerate(links, start=1):
        load = Loader(link)
        title = load.download_audio()

        start_t = time.time()
        print(f"whisper started {i}/{len(links)}...")
        model = whisper.load_model("base")
        result = model.transcribe(title)

        if title.endswith(".mp4"):
            title = title.replace(".mp4", ".txt")

        with open(title, "w") as file:
            file.write(result['text'])

        print(f"total time for whisper transcription: {round(time.time() - start_t, 2)} sec.")
        print(f"Transcription saved\ntitle: {title}\n")


if __name__ == "__main__":
    main()
