import asyncio
import copy
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Any

import yt_dlp
from loguru import logger
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from objects import DownloadTask


class YouTubeLoader:
    """
    Singleton client loader.
    Using yt_dlp and youtube_transcript_api libs.
    internal settings: ThreadPoolExecutor workers number
    """

    _instance = None
    __config: dict[str, Any] = {
        "quiet": True,
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, directory: Path):
        self.dir = directory
        self.pool_heavy = ThreadPoolExecutor(max_workers=20)
        self.pool_light = ThreadPoolExecutor(max_workers=40)
        logger.info("YouTubeLoader initialized")

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
    def _async_wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):  # ANN202
            loop = asyncio.get_running_loop()
            if func.__name__ == "get_captions":
                return await loop.run_in_executor(self.pool_light, lambda: func(self, *args, **kwargs))
            return await loop.run_in_executor(self.pool_heavy, lambda: func(self, *args, **kwargs))

        return wrapper

    @_async_wrap
    def download_audio(self, task: DownloadTask) -> DownloadTask:
        """
        Downloads audio from the YouTube video.
        :param task: DownloadTask
        :return: filled DownloadTask
        """
        title = f"{task.id}{self.prepare_title(task.video.title)}"
        config = copy.deepcopy(self.__config)
        config["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
        ext = config["postprocessors"][0]["preferredcodec"]
        config["format"] = "bestaudio[ext=m4a]/best"
        config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([task.video.link])
                task.result = True
                task.local_path = Path(f"{self.dir}/{title}.{ext}")
                task.file_size = task.local_path.stat().st_size
                logger.info(f"{task.id} Audio downloaded to {self.dir}/{title}.{ext}")
        except yt_dlp.utils.DownloadError:
            logger.error(f"{task.id} Exception during audio download for video id: {task.video.id}")
            task.message.message["ru"] = "Произошла ошибка при скачивании аудио файла"
            task.result = False

        return task

    @_async_wrap
    def download_video(self, task: DownloadTask) -> DownloadTask:
        """
        Downloads video from the YouTube video.
        :param task: DownloadTask
        :return: filled DownloadTask
        """
        title = f"{task.id}{self.prepare_title(task.video.title)}"
        config = copy.deepcopy(self.__config)
        config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        config["format"] = (
            f"bestvideo[height<={task.options.height}][ext={task.options.extension}][fps<={task.options.fps}]+bestaudio[ext=m4a]/worst"
        )

        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([task.video.link])
                logger.info(f"{task.id} Video downloaded to {self.dir}/{title}.{task.options.extension}")
                task.local_path = Path(f"{self.dir}/{title}.{task.options.extension}")
                task.file_size = task.local_path.stat().st_size
                task.result = True
        except Exception as e:
            logger.error(f"{task.id} Exception during video download for video id: {task.video.id}, {e.__repr__()}")
            task.message.message["ru"] = "Произошла ошибка при скачивании видео файла"
            task.result = False

        return task

    @_async_wrap
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

            logger.info(f"{task.id} Successfully got a transcript for video: {task.video.id}")

        except (NoTranscriptFound, TranscriptsDisabled, Exception) as e:
            logger.error(f"{task.id} {e.__repr__()}")
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
        logger.info(f"{task.id} Transcript saved to: {target_path}")
        task.local_path = target_path
        task.file_size = task.local_path.stat().st_size
        task.result = True
        return task
