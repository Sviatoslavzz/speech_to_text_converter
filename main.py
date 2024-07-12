import whisper
# from pytube_loader import Loader
from yt_dlp_loader import Yt_loader
import time
import warnings
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


def collect_links() -> list:
    links = []
    print("Please provide YouTube video links each on new and press enter:")
    links.append(input())
    link = input()
    while link != "":
        links.append(link)
        link = input()
    return links


def transcribe(directory: str, link: str, model):
    loader = Yt_loader(link)
    title, is_loaded = loader.download_audio()
    if is_loaded:
        result = model.transcribe(title)
        if title.endswith(".mp3"):
            title = title.replace(".mp3", ".txt")
            with open(f'{directory}/{title}', "w") as file:
                file.write(result['text'])
            print(f"Transcription saved\ntitle: {title}\n")
        else:
            print("Please check audio extension")


def main():
    directory = 'saved_files'
    if not os.path.exists(directory):
        os.makedirs(directory)

    links = collect_links()
    print("starting loop...")
    start_t = time.time()
    model = whisper.load_model("base")

    max_workers = len(links)
    if max_workers > 4:
        max_workers = 4
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        link_iter = iter(links)

        for _ in range(max_workers):
            try:
                link = next(link_iter)
                futures.append(executor.submit(transcribe, directory, link, model))
            except StopIteration:
                break

        completed_count = 0
        while futures:
            for future in as_completed(futures):
                futures.remove(future)
                try:
                    future.result()  # This will raise any exceptions encountered in transcribe
                    completed_count += 1
                    print(f"whisper completed {completed_count}/{len(links)}\n")
                except Exception as e:
                    print(f"Error processing link: {e}")

                # Submit a new task if there are more links to process
                try:
                    link = next(link_iter)
                    futures.append(executor.submit(transcribe, directory, link, model))
                except StopIteration:
                    continue

    # for i, link in enumerate(links, start=1):
    #     print(f"whisper started {i}/{len(links)}...")
    #     transcribe(directory, link, model)

    print(f"total time : {round(time.time() - start_t, 2)} sec.")


if __name__ == "__main__":
    main()
