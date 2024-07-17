# from pytube_loader import Loader
import time
import warnings
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from channel_link_collector import get_channel_videos, get_channel_id_by_name
from transcriber import Transcriber

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


def collect_links() -> list:
    links = []
    channel_link = input(
        """You can enter a channel link to collect all videos from a channel, """
        """or press enter to proceed with simple links:\n""")
    if "youtube.com" in channel_link:
        try:
            amount, links = get_channel_videos(get_channel_id_by_name(channel_link))
            print(f"Собрано {amount} ссылок на видео")
        except ValueError as e:
            print(f"Ups: {e}")
    else:
        print("Please provide YouTube video links each on new and press enter:")
        links.append(input())
        link = input()
        while link != "":
            if "youtube.com" in link:
                links.append(link)
            link = input()
    return links


def main():
    directory = 'saved_files'
    if not os.path.exists(directory):
        os.makedirs(directory)

    links = collect_links()

    print("starting loop...")
    start_t = time.time()
    # model = whisper.load_model("base")
    transcriber = Transcriber()
    max_workers = len(links)
    if max_workers > 4:
        max_workers = 4
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        link_iter = iter(links)

        for _ in range(max_workers):
            try:
                link = next(link_iter)
                futures.append(executor.submit(transcriber.transcribe, directory, link))
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
                    futures.append(executor.submit(transcriber.transcribe, directory, link))
                except StopIteration:
                    continue

    print(f"total time : {round(time.time() - start_t, 2)} sec.")


if __name__ == "__main__":
    main()
