import asyncio
from collections import OrderedDict
from collections.abc import Callable
from pathlib import Path

from loguru import logger

from app_worker import AppWorker
from config.base import YAMLConfig
from config.conf_models import BaseConfig
from objects import DownloadOptions, DownloadTask, TranscriptionTask, VideoOptions, YouTubeVideo
from parser import get_parser
from transcribers.transcriber_worker import TranscriberWorker


async def collect_videos() -> list[YouTubeVideo | None]:
    """
    Collects YouTubeVideo objects by provided links
    """
    videos = []
    chooser = input("Please choose a mode:\n1. channel link\n2. video link(s)\n")
    if chooser not in ["1", "2"]:
        return videos

    if chooser == "1":
        channel = input("Please provide a channel link: ")
        result, amount, videos = await AppWorker.get_instance().get_channel_videos(channel)
        if not result:
            logger.warning("Не нашел канал по данной ссылке")
        elif not amount:
            logger.warning("Не нашел видео на данном канале")
        else:
            logger.info(f"Нашел {amount} видео на канале {videos[0].owner_username} ✅")
    else:
        user_input = ""
        while True:
            link = input("Please provide a next link or an empty input to process\n")
            if not link:
                break
            user_input += f"{link} "
        async for result, link, video in AppWorker.get_instance().convert_links_to_videos(user_input):
            if not result:
                logger.warning(f"не нашел видео поссылке {link}")
                continue
            logger.info(f"нашел видео {video.title}")
            videos.append(video)

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


async def cli_task_completion_loop(coroutines: list):
    for complete_task in asyncio.as_completed(coroutines):
        result_task: DownloadTask = await complete_task
        await asyncio.sleep(0.5)
        if result_task.result:
            print(f"successfully downloaded: {result_task.video.title} to {result_task.local_path}")
        else:
            print(f"failed to download: {result_task.video.title}")


async def _download(worker: Callable,
                    videos: list[YouTubeVideo],
                    options: VideoOptions | None = None):
    coroutines = AppWorker.get_instance().launch_coroutines(
        async_worker=worker,
        id_="",
        videos=videos,
        options=options or VideoOptions(),
    )
    await cli_task_completion_loop(coroutines)


def get_options_from_user() -> VideoOptions | None:
    standard_options = OrderedDict()
    standard_options["1"] = {"message": "144p - 30 fps", "options": "256:144:30"}
    standard_options["2"] = {"message": "240p - 30 fps", "options": "426:240:30"}
    standard_options["3"] = {"message": "360p - 30 fps", "options": "640:360:30"}
    standard_options["4"] = {"message": "480p - 30 fps", "options": "854:480:30"}
    standard_options["5"] = {"message": "720p - 30 fps", "options": "1280:720:30"}
    standard_options["6"] = {"message": "720p - 60 fps", "options": "1280:720:60"}
    standard_options["7"] = {"message": "1080p - 30 fps", "options": "1920:1080:30"}
    standard_options["8"] = {"message": "1080p - 60 fps", "options": "1920:1080:60"}
    standard_options["9"] = {"message": "1440p - 30 fps", "options": "2560:1440:30"}
    standard_options["10"] = {"message": "1440p - 60 fps", "options": "2560:1440:60"}
    standard_options["11"] = {"message": "2160p - 30 fps", "options": "3840:2160:30"}
    standard_options["12"] = {"message": "2160p - 60 fps", "options": "3840:2160:60"}

    print("Choose a common option for all videos (applied <= chosen)\n")
    for k, v in standard_options.items():
        print(f"{k}: {v['message']}")

    u_option = input()
    if u_option not in standard_options:
        print("wrong option, using default...")
        return None
    width, height, fps = map(int, standard_options[u_option]["options"].split(":"))
    return VideoOptions(width=width, height=height, fps=fps)


async def get_options_dynamic(video: YouTubeVideo) -> VideoOptions | None:
    options = await AppWorker.get_instance().get_video_options(video)

    print("Choose an option for downloading:")

    for i, option in enumerate(options, start=1):
        print(f"{i}: {option.width}x{option.height} fps={option.fps}")

    try:
        chooser = int(input())
        if chooser > len(options) or chooser <= 0:
            raise ValueError
    except ValueError:
        print("wrong option, using default...")
        return None

    return options[chooser - 1]


async def _run_cli():
    parser = get_parser()
    args = parser.parse_args()
    config: YAMLConfig = args.config
    conf_data: BaseConfig = config.data
    conf_data.bot.server = "local"  # to avoid external storage run

    worker = AppWorker(conf_data)

    chooser = input("Please choose the mode:\n1: transcribe from a file\n2: load from YouTube\n")

    match chooser:
        case "1":
            source_filename = input("Please provide an absolute path to file:\n")
            try:
                path_ = Path(source_filename)
                if not path_.is_file():
                    raise FileNotFoundError
            except FileNotFoundError:
                print("file not found")
                return

            task = TranscriptionTask(id="", origin_path=path_)
            transcriber = TranscriberWorker(config=conf_data.transcriber)
            task = await transcriber.transcribe(task)
            if task.result:
                logger.info(f"Transcription is saved to {task.local_path}")
            else:
                logger.error("Unable to make a transcription")
        case "2":
            videos = await collect_videos()
            if not videos:
                print(">> You did not enter any link! <<")
                return

            menu_opt = menu()
            if menu_opt == DownloadOptions.TEXT:
                await _download(worker.download_subtitles_worker, videos)
            elif menu_opt == DownloadOptions.VIDEO:
                if len(videos) > 1:
                    options = get_options_from_user()
                else:
                    options = await get_options_dynamic(videos[0])
                await _download(worker.download_video_worker, videos, options)
            elif menu_opt == DownloadOptions.AUDIO:
                await _download(worker.download_video_worker, videos)
        case _:
            print("Sorry, you entered a wrong option")


def cli():
    asyncio.run(_run_cli())
