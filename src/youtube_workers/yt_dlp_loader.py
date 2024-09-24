import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import yt_dlp
from loguru import logger
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from objects import YouTubeVideo


class YouTubeLoader:
    __config: dict[str, Any] = {
        "quiet": True,
    }

    def __init__(self, directory: Path):
        self.dir = directory
        self.semaphore = asyncio.Semaphore(20)
        self.pool = ThreadPoolExecutor(max_workers=20)
        logger.info("YouTubeLoader initialized")

    @staticmethod
    def prepare_title(title: str) -> str:
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

    def _sync_download_audio(self, video: YouTubeVideo) -> (bool, Path):
        title = self.prepare_title(video.title)
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
                ydl.download([video.generate_link()])
                logger.info(f"Audio downloaded to {self.dir}/{title}.{ext}")
                return True, Path(f"{self.dir}/{title}.{ext}")
        except yt_dlp.utils.DownloadError:
            logger.error(f"Exception during audio download for video id: {video.id}")
            return False, Path()

    async def download_audio(self, video: YouTubeVideo) -> (bool, Path):
        """
        Downloads audio from the YouTube video.
        :param video: YouTubeVideo instance with the checked video meta
        :return:
        """
        async with self.semaphore:
            return await self.__run_async(video, self._sync_download_audio)

    def _sync_download_video(
            self, video: YouTubeVideo, required_ext: str = "mp4", required_height: int | None = 720, fps_limit: int = 30
    ) -> (bool, Path):
        video.generate_link()

        title = self.prepare_title(video.title)
        config = copy.deepcopy(self.__config)
        config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        config["format"] = (
            f"bestvideo[height<={required_height}][ext={required_ext}][fps<={fps_limit}]+bestaudio[ext=m4a]/worst"
        )

        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([video.link])
                logger.info(f"Video downloaded to {self.dir}/{title}.{required_ext}")

                return True, Path(f"{self.dir}/{title}.{required_ext}")

        except yt_dlp.utils.DownloadError:
            logger.error(f"Exception during video download for video id: {video.id}")
        except Exception as e:
            logger.error(f"Exception during video download for video id: {video.id}, {e.__repr__()}")

        return False, Path()

    async def download_video(
            self,
            video: YouTubeVideo,
            required_ext: str = "mp4",  # TODO дописать конвертацию в требуемый формат если не найден
            required_height: int = 720,
            fps_limit: int = 30,
    ) -> (bool, Path):
        """
        Downloads video from the YouTube video.
        :param video: YouTubeVideo instance with the checked video meta
        :param required_ext: required video format (like mp4 or webm)
        :param required_height: required quality
        :param fps_limit: 30 or 60
        :return:
        """
        async with self.semaphore:
            return await self.__run_async(video, self._sync_download_video, required_ext, required_height, fps_limit)

    async def __run_async(
            self, video: YouTubeVideo, function, *args) -> (bool, Path):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.pool, function, video, *args)

    async def get_captions(
            self,
            video: YouTubeVideo,
            preferred_language: str | None = "ru"
    ) -> (bool, Path):
        """
        Downloads captions from the YouTube video.
        :param video: YouTubeVideo instance with the checked video meta
        :param preferred_language: e.g. "ru"
        :return: bool, Path
        """
        async with self.semaphore:
            return await self.__run_async(video, self._sync_get_captions, preferred_language)

    def _sync_get_captions(self, video: YouTubeVideo, preferred_language: str | None = "ru") -> (bool, Path):
        title = self.prepare_title(video.title)
        transcript = None

        try:
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id=video.id)
            transcript_obj_any = None
            for transcript_obj in available_transcripts:
                transcript_obj_any = transcript_obj
                if transcript_obj.language_code == preferred_language:
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

            logger.info(f"Successfully got a transcript for video: {video.id}")

        except (NoTranscriptFound, TranscriptsDisabled, Exception) as e:
            logger.error(f"{e.__repr__()}")

            return False, Path()

        target_path: Path = (self.dir / title).with_suffix(".txt")
        with target_path.open("w", encoding="utf-8") as file:
            for entry in transcript:
                file.write(entry["text"].replace("\n", "") + " ")
        logger.info(f"Transcript saved to: {target_path}")

        return True, target_path
