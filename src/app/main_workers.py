import os
from pathlib import Path
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
import re

from loguru import logger

from youtube_workers.yt_dlp_loader import YouTubeLoader
from youtube_workers.youtube_api import YouTubeClient

SAVING_FOLDER = "saved_files"


def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API")}


def make_save_dir() -> Path:
    absolute_path = Path(__file__).absolute().parent.parent.parent
    dir_ = Path(f"{absolute_path}/{SAVING_FOLDER}")
    if not dir_.is_dir():
        dir_.mkdir()
        logger.info(f"Saving directory created: {dir_}")
    logger.info(f"Saving directory set up: {dir_}")
    return dir_


async def download_video_worker(options: dict[str, Any]) -> AsyncGenerator[tuple[bool, Path], None]:
    directory: Path = make_save_dir()

    youtube_client = YouTubeClient(get_env().get("YOUTUBE_API"))
    youtube_loader = YouTubeLoader(directory)

    if options["option"] == "video":  # video, file, channel
        links = re.split(r'[ ,\n]+', options["links"])
        for link in links:
            video = await youtube_client.get_video_by_link(link)
            if not video:
                yield False, link
            else:
                yield await youtube_loader.download_video(video, required_height=480)

    elif options["option"] == "channel":
        channel_id = await youtube_client.get_channel_id_by_link(options["links"])
        if not channel_id:
            yield False, options["links"]
        else:
            amount, videos = await youtube_client.get_channel_videos(channel_id)
            if not videos:
                yield False, options["links"]
            else:
                for video in videos:
                    yield await youtube_loader.download_video(video, required_height=480)
