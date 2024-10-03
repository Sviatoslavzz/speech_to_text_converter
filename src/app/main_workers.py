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


async def channel_worker(options: dict[str, Any]) -> AsyncGenerator[tuple[bool, Path], None]:
    youtube_client = YouTubeClient(get_env().get("YOUTUBE_API")) \
        if not YouTubeClient.get_instance() \
        else YouTubeClient.get_instance()

    youtube_loader = YouTubeLoader(make_save_dir()) \
        if not YouTubeLoader.get_instance() \
        else YouTubeLoader.get_instance()

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


async def download_video_worker(options: dict[str, Any]) -> AsyncGenerator[tuple[bool, Path], None]:
    youtube_client = YouTubeClient(get_env().get("YOUTUBE_API")) \
        if not YouTubeClient.get_instance() \
        else YouTubeClient.get_instance()

    youtube_loader = YouTubeLoader(make_save_dir()) \
        if not YouTubeLoader.get_instance() \
        else YouTubeLoader.get_instance()

    links = re.split(r'[ ,\n]+', options["links"])
    for link in links:
        video = await youtube_client.get_video_by_link(link.strip())
        if not video:
            yield False, link
        else:
            yield await youtube_loader.download_video(video, required_height=480)


async def download_audio_worker(options: dict[str, Any]) -> AsyncGenerator[tuple[bool, Path], None]:
    youtube_client = YouTubeClient(get_env().get("YOUTUBE_API")) \
        if not YouTubeClient.get_instance() \
        else YouTubeClient.get_instance()

    youtube_loader = YouTubeLoader(make_save_dir()) \
        if not YouTubeLoader.get_instance() \
        else YouTubeLoader.get_instance()

    links = re.split(r'[ ,\n]+', options["links"])
    for link in links:
        video = await youtube_client.get_video_by_link(link.strip())
        if not video:
            yield False, link
        else:
            yield await youtube_loader.download_audio(video)


async def download_subtitles_worker(options: dict[str, Any]) -> AsyncGenerator[tuple[bool, Path], None]:
    youtube_client = YouTubeClient(get_env().get("YOUTUBE_API")) \
        if not YouTubeClient.get_instance() \
        else YouTubeClient.get_instance()

    youtube_loader = YouTubeLoader(make_save_dir()) \
        if not YouTubeLoader.get_instance() \
        else YouTubeLoader.get_instance()

    links = re.split(r'[ ,\n]+', options["links"])
    for link in links:
        video = await youtube_client.get_video_by_link(link.strip())
        if not video:
            yield False, link
        else:
            yield await youtube_loader.get_captions(video)
