# from pytube_loader import Loader
import warnings
import os
import asyncio

from captions import get_caption_by_link
from youtube_api import get_channel_videos, get_channel_id_by_name
from transcriber import Transcriber
from objects import DownloadOptions
from yt_dlp_loader import Yt_loader

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


def make_save_dir() -> str:
    dir_ = 'saved_files'
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    return dir_


def collect_links() -> list:
    links = []
    channel_link = input(
        """You can enter a channel link to collect all videos from a channel, """
        """or press enter to proceed with simple links:\n""")
    if "youtube.com" in channel_link:
        try:
            amount, links = get_channel_videos(get_channel_id_by_name(channel_link.strip()))
            print(f"Собрано {amount} ссылок на видео")
        except ValueError as e:
            print(f"Ups: {e}")
    else:
        print("Please provide YouTube video links each on new line and press enter:")
        link = input()
        while link != "":
            if "youtube.com" in link:
                links.append(link.strip())
            link = input()
    return links


def menu():
    option = -1
    while option != '4' and option != "exit":
        print("Please choose options to continue\n1. Download text\n2. Download audio\n3. Download video\n4. Exit")
        option = input()

        if not option.isdigit():
            option = -1

        if int(option) == DownloadOptions.TEXT.value:
            return DownloadOptions.TEXT
        elif int(option) == DownloadOptions.AUDIO.value:
            return DownloadOptions.AUDIO
        elif int(option) == DownloadOptions.VIDEO.value:
            return DownloadOptions.VIDEO
        elif option != '4' and option != "exit":
            print("Sorry, you entered a wrong option")


async def process_links(directory: str, links: list) -> None:
    tasks = []
    transcriber = Transcriber()
    for link in links:
        tasks.append(get_caption_by_link(directory, link))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for link, result in zip(links, results):
        if not result:
            await asyncio.get_event_loop().run_in_executor(None, transcriber.transcribe_audio, directory, link)


def main():
    directory = make_save_dir()
    links = collect_links()

    if not links:
        print(">> You did not enter any link! <<")
        return

    menu_opt = menu()
    if menu_opt == DownloadOptions.TEXT:
        asyncio.run(process_links(directory, links))
    elif menu_opt == DownloadOptions.VIDEO:
        quality = input("Enter a quality e.g. 720p: ")
        loader = Yt_loader(directory)
        for link in links:
            loader.download_video(link, quality=quality)
    elif menu_opt == DownloadOptions.AUDIO:
        loader = Yt_loader(directory)
        for link in links:
            loader.download_audio(link)


if __name__ == "__main__":
    main()
