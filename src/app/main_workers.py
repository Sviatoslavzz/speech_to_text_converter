import os
from pathlib import Path
from typing import Any, AsyncGenerator

from dotenv import load_dotenv
import re

from loguru import logger

from objects import YouTubeVideo
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


def get_clients() -> tuple[YouTubeClient, YouTubeLoader]:
    youtube_client = YouTubeClient(get_env().get("YOUTUBE_API")) \
        if not YouTubeClient.get_instance() \
        else YouTubeClient.get_instance()

    youtube_loader = YouTubeLoader(make_save_dir()) \
        if not YouTubeLoader.get_instance() \
        else YouTubeLoader.get_instance()

    return youtube_client, youtube_loader


async def convert_links_to_videos(links: str) -> AsyncGenerator[tuple[bool, str, YouTubeVideo | None], None]:
    links = re.split(r'[ ,\n]+', links)
    youtube_client, _ = get_clients()
    for link in links:
        video = await youtube_client.get_video_by_link(link.strip())
        if not video:
            yield False, link, None
        else:
            yield True, link, video


async def get_channel_videos_worker(link: str) -> tuple[bool, int, list[YouTubeVideo] | None]:
    youtube_client, _ = get_clients()
    channel_id = await youtube_client.get_channel_id_by_link(link.strip())
    if not channel_id:
        return False, 0, None
    amount, videos = await youtube_client.get_channel_videos(channel_id)
    return True, amount, videos


async def download_video_worker(videos: list[YouTubeVideo], chat_id:str) -> AsyncGenerator[tuple[bool, Path], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.download_video(video=video, required_height=480, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link


async def download_audio_worker(videos: list[YouTubeVideo], chat_id:str) -> AsyncGenerator[tuple[bool, Path], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.download_audio(video=video, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link


async def download_subtitles_worker(videos: list[YouTubeVideo], chat_id:str) -> AsyncGenerator[tuple[bool, Path | str], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.get_captions(video=video, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link
