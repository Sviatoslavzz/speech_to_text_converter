import asyncio
import copy
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Any

import yt_dlp
from loguru import logger
from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi

from objects import DownloadTask, VideoOptions


class YouTubeLoader:
    """
    Singleton loader client.
    `yt_dlp` and `youtube_transcript_api` libs are used.

    Runs loading tasks asynchronously in threads.
    pool_heavy - for audio and video loading.
    pool_light - for transcript loading.
    """

    _instance = None
    __config: dict[str, Any] = {
        "quiet": True,
        "socket_timeout": 5,
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, directory: Path, heavy_pool_size: int, light_pool_size: int, proxy: str | None = None):
        self.dir = directory
        self.pool_heavy = ThreadPoolExecutor(max_workers=heavy_pool_size)
        self.pool_light = ThreadPoolExecutor(max_workers=light_pool_size)
        if proxy:
            self.__config["proxy"] = proxy

        logger.info("{cls} : initialized : heavy_pool_size={heavy} : light_pool_size={light}",
                    cls=self.__class__.__name__,
                    heavy=heavy_pool_size,
                    light=light_pool_size)

    @classmethod
    def get_instance(cls):
        return cls._instance

    @staticmethod
    def prepare_title(title: str) -> str:
        """
        Normalizes a string to make it lowercase consisting of letters, digits and underscores.
        :param title: a string to normalize
        :return: str
        """
        new_title = ""
        flag_fill = True
        for letter in title:
            if letter.isalpha() or letter.isdigit():
                new_title += letter
                flag_fill = True
            elif flag_fill:
                new_title += "_"
                flag_fill = False

        return new_title.strip("_").lower()

    @staticmethod
    def __async_wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):  # ANN202
            loop = asyncio.get_running_loop()
            if func.__name__ in ["get_captions", "get_video_options"]:
                return await loop.run_in_executor(self.pool_light, lambda: func(self, *args, **kwargs))
            return await loop.run_in_executor(self.pool_heavy, lambda: func(self, *args, **kwargs))

        return wrapper

    @__async_wrap
    def get_video_options(self, link: str) -> list[VideoOptions]:
        """
        Loads and sorts all available video formats with the highest vbr (video bitrate).
        :param link: YouTube video link
        :return: list of video options or empty list
        """
        resolution_dict = {}
        try:
            with yt_dlp.YoutubeDL(self.__config) as ydl:
                info_dict = ydl.extract_info(link, download=False)
                formats = info_dict.get("formats", [])
                for f in formats:
                    if (
                            f.get("downloader_options")
                            and f.get("fps")
                            and f.get("width")
                            and f.get("height")
                            and f.get("ext") == "mp4"
                            and f.get("vbr")
                    ):
                        cur_key = VideoOptions(width=f.get("width"), height=f.get("height"), fps=f.get("fps"))
                        if resolution_dict.get(cur_key) and resolution_dict[cur_key] < f.get("vbr"):
                            resolution_dict[cur_key] = f.get("vbr")
                        else:
                            resolution_dict[cur_key] = f.get("vbr")
                logger.info("Successfully got options for video {link}", link=link)
        except Exception as e:
            logger.error("Exception during extracting video info: {err}", err=e.__repr__())

        return list(resolution_dict)

    @__async_wrap
    def download_audio(
            self, task: DownloadTask, format_: str = "mp3", quality: str = "best", yt_dlp_config: dict | None = None
    ) -> DownloadTask:
        """
        Downloads audio from the YouTube video.
        :param quality: best | worst
        :param format_: mp3 or m4a
        :param yt_dlp_config: optional configuration for YoutubeDL
        :param task: DownloadTask
        :return: updated DownloadTask
        """
        title = f"{task.id}{self.prepare_title(task.video.title)}"
        config = yt_dlp_config if yt_dlp_config else copy.deepcopy(self.__config)
        ext = format_
        if format_ == "mp3":
            config["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
            ext = config["postprocessors"][0]["preferredcodec"]
        config["format"] = f"{quality}audio[ext=m4a]/{quality}"
        config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([task.video.link])
                task.result = True
                task.local_path = Path(f"{self.dir}/{title}.{ext}")
                task.file_size = task.local_path.stat().st_size
                logger.info("{task} Audio downloaded to {dir}/{title}.{ext}",
                            task=task.id, dir=self.dir, title=title, ext=ext)
        except Exception as e:
            logger.error("{task} Exception during audio download for video id: {video} {err}",
                         task=task.id, video=task.video.id, err=e.__repr__())
            task.message.message["ru"] = "Произошла ошибка при скачивании аудио файла"
            task.message.message["en"] = "Error during audio download"
            task.result = False

        return task

    @__async_wrap
    def download_video(self, task: DownloadTask, yt_dlp_config: dict | None = None) -> DownloadTask:
        """
        Downloads video from the YouTube video.
        Fills task with a path, result, message.
        :param yt_dlp_config: optional configuration for YoutubeDL
        :param task: DownloadTask
        """
        title = f"{task.id}{self.prepare_title(task.video.title)}"
        config = yt_dlp_config if yt_dlp_config else copy.deepcopy(self.__config)
        config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        config[
            "format"
        ] = f"""bestvideo[height<={task.options.height}][width<={task.options.width}][ext={task.options.extension}]
[fps<={task.options.fps}]+bestaudio[ext=m4a]/worst"""

        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([task.video.link])
                task.local_path = Path(f"{self.dir}/{title}.{task.options.extension}")
                task.file_size = task.local_path.stat().st_size
                task.result = True
                logger.info("{task} Video downloaded to {dir}/{title}.{ext}",
                            task=task.id, dir=self.dir, title=title, ext=task.options.extension)
        except Exception as e:
            logger.error("{task} Exception during video download for video id: {video}, {err}",
                         task=task.id, video=task.video.id, err=e.__repr__())
            task.message.message["ru"] = "Произошла ошибка при скачивании видео файла"
            task.message.message["ru"] = "Error during video download"
            task.result = False

        return task

    @__async_wrap
    def get_captions(self, task: DownloadTask) -> DownloadTask:
        """
        Downloads captions from the YouTube video.
        :param task: DownloadTask
        :return: filled DownloadTask
        """
        title = f"{task.id}{self.prepare_title(task.video.title)}"
        transcript = None

        try:
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id=task.video.id)
            transcript_obj_any = None
            for transcript_obj in available_transcripts:
                transcript_obj_any = transcript_obj
                if transcript_obj.language_code == task.options.language:
                    transcript = transcript_obj.fetch()
                    break
            if (
                    not transcript and transcript_obj_any and transcript_obj_any.is_translatable
            ):  # TODO загружает [music]...
                transcript = transcript_obj_any.translate("en").fetch()
            elif not transcript and transcript_obj_any:
                transcript = transcript_obj_any.fetch()
            elif not transcript:
                raise NoTranscriptFound

            logger.info("{task} Successfully got a transcript for video: {video}",
                        task=task.id, video=task.video.id)

        except Exception as e:
            logger.warning("{task} {err}", task=task.id, err=e.__repr__())
            task.message.message["ru"] = f"Не нашел субтитры для видео {task.video.id}"
            task.result = False
            return task

        target_path: Path = (self.dir / title).with_suffix(".txt")
        with target_path.open("w", encoding="utf-8") as file:
            file.write(f"Название: {task.video.title}\n")
            file.write(f"Автор: {task.video.owner_username}\n")
            file.write(f"Дата публикации: {task.video.published_at}\n\n")
            for entry in transcript:
                file.write(entry["text"].replace("\n", "") + " ")
        logger.info("{task} Transcript saved to: {path}", task=task.id, path=target_path)
        task.local_path = target_path
        task.file_size = task.local_path.stat().st_size
        task.result = True
        return task
