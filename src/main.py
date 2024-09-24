import asyncio
from pathlib import Path

from loguru import logger
from dotenv import load_dotenv
import os
from objects import DownloadOptions, YouTubeVideo
from transcribers.abscract import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber
from youtube_workers.youtube_api import YouTubeClient
from youtube_workers.yt_dlp_loader import YouTubeLoader

# TODO добавление через config
WHISPER_MODEL = "small"
SAVING_FOLDER = "saved_files"
TRANSCRIBER: type[AbstractTranscriber] = FasterWhisperTranscriber


def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API")}


def make_save_dir() -> Path:
    absolute_path = Path(__file__).absolute().parent.parent
    dir_ = Path(f"{absolute_path}/{SAVING_FOLDER}")
    if not dir_.is_dir():
        dir_.mkdir()
        logger.info(f"Saving directory created: {dir_}")
    logger.info(f"Saving directory set up: {dir_}")
    return dir_


async def collect_videos() -> list:
    client = YouTubeClient(get_env().get("YOUTUBE_API"))  # TODO change to config

    videos: list[YouTubeVideo] = []
    channel_link = input(
        """You can enter a channel link to collect all videos from a channel, """
        """or press enter to proceed with simple links:\n"""
    )
    if "youtube.com" in channel_link:
        channel_id = await client.get_channel_id_by_link(channel_link)
        if channel_id:
            amount, videos = await client.get_channel_videos(channel_id)
            logger.info(f"Collected {amount} videos from channel {channel_id}")
    else:
        print("Please provide YouTube video links each on new line and press enter:")
        link = input()
        while link != "":
            if "youtube.com" in link:
                video = await client.get_video_by_link(link.strip())
                if video:
                    videos.append(video)
            link = input()
    return videos


def menu() -> DownloadOptions:
    while True:
        print("Please choose options to continue\n1. Download text\n2. Download audio\n3. Download video\n4. Exit")
        option = input()

        if not option.isdigit():
            option = -1

        if int(option) == DownloadOptions.TEXT.value:
            return DownloadOptions.TEXT
        if int(option) == DownloadOptions.AUDIO.value:
            return DownloadOptions.AUDIO
        if int(option) == DownloadOptions.VIDEO.value:
            return DownloadOptions.VIDEO
        if option == "4":
            return DownloadOptions.EXIT
        print("Sorry, you entered a wrong option")


def transcriber_saver(transcriber: AbstractTranscriber, save_dir: Path, file_name: str) -> None:
    """
    Checks the save_dir, launches transcription process, saves the result in .txt
    :param transcriber: current class
    :param save_dir: saving directory
    :param file_name: source file
    :return: None
    """
    source_path = save_dir / file_name
    if not source_path.is_file():
        logger.error(f"File does not exist: {source_path}")
        raise FileNotFoundError(f"{source_path} not found")

    result = transcriber.transcribe(path=source_path)
    target_file = source_path.with_suffix(".txt")

    try:
        with target_file.open(mode="w") as file:
            file.write(result)
        logger.info(f"Transcription saved\ntitle: {target_file}\n")
    except OSError as err:
        logger.error(f"Unable to save transcription to {target_file}")
        raise OSError("Failed to save transcription") from err


# async def process_links(save_dir: Path, links: list[str]) -> None:
#     """
#     Tries to get captions by YT video link, in case of fail tries to transcribe loaded audio file to text
#     :param save_dir: directory to save the transcribed videos
#     :param links: list of links
#     :return: None
#     """
#     tasks = [get_caption_by_link(save_dir, link) for link in links]
#     logger.info("Subtitles loading process is started")
#
#     results = await asyncio.gather(*tasks, return_exceptions=True)
#
#     tasks_to_download = []
#     loader = YouTubeLoader(save_dir)
#     for link, result in zip(links, results, strict=False):
#         if not result:
#             logger.info("Found new link to download, adding...")
#             tasks_to_download.append(loader.async_download_audio(link))
#     results_to_download = await asyncio.gather(*tasks_to_download, return_exceptions=True)
#
#     transcriber = None
#     for file_path, success in results_to_download:
#         if success:
#             if not transcriber:
#                 transcriber = TRANSCRIBER(model=WHISPER_MODEL)
#                 logger.info(f"Transcriber {transcriber.__class__.__name__} initialized")
#             logger.info("Create new thread for transcription")
#             await asyncio.get_running_loop().run_in_executor(None, transcriber_saver, transcriber, save_dir, file_path)


async def main() -> None:
    directory: Path = make_save_dir()
    loader = YouTubeLoader(directory)

    chooser = input("Please choose the mode: 1 - file, 2 - youtube\n")
    if chooser == "1":
        logger.info("File mode chosen")
        source_filename = input("please input path:\n")
        logger.info(f"Source file name is: {source_filename}")
        transcriber = TRANSCRIBER(WHISPER_MODEL)
        transcriber_saver(transcriber, directory, source_filename)
    elif chooser == "2":
        videos = await collect_videos()
        if not videos:
            print(">> You did not enter any link! <<")
            return
        menu_opt = menu()
        if menu_opt == DownloadOptions.TEXT:
            for video in videos:
                await loader.get_captions(video)
            # asyncio.run(process_links(directory, videos))
        elif menu_opt == DownloadOptions.VIDEO:
            quality = int(input("Enter a quality e.g. 720: "))
            for video in videos:
                await loader.download_video(video, required_height=quality)
        elif menu_opt == DownloadOptions.AUDIO:
            for video in videos:
                await loader.download_audio(video)


if __name__ == "__main__":
    asyncio.run(main())
