import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yt_dlp
from loguru import logger

from objects import YouTubeVideo


class YouTubeLoader:
    _audio_config = {
        "format": "bestaudio/best",  # the best audio quality available
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",  # Quality in kbps (e.g., 192)
            }
        ],
        "outtmpl": "",  # Output filename template
        "quiet": True,
    }

    __config = {
        "quiet": True,
    }

    def __init__(self, directory: Path):
        self.dir = directory
        self.semaphore = asyncio.Semaphore(20)
        self.pool = ThreadPoolExecutor(max_workers=20)
        logger.info("YouTubeLoader initialized")

    @staticmethod
    def prepare_title(title: str) -> str:
        # title = title.encode("utf-8").decode("utf-8")
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

    def sync_download_audio(self, video: YouTubeVideo) -> (bool, Path):
        title = self.prepare_title(video.title)
        config = copy.deepcopy(self._audio_config)
        ext = config["postprocessors"][0]["preferredcodec"]
        config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([video.generate_link()])
                logger.info(f"Audio downloaded to {self.dir}/{title}.{ext}")
                return True, Path(f"{self.dir}/{title}.{ext}")
        except yt_dlp.utils.DownloadError:
            logger.error(f"Exception during audio download for video id: {video.id}")
            return False, Path("")

    async def download_audio(self, video: YouTubeVideo) -> (bool, Path):
        """
        Downloads audio from the YouTube video.
        :param video: YouTubeVideo instance with the checked video meta
        :return:
        """
        async with self.semaphore:
            return await self._download_audio(video)

    async def _download_audio(self, video: YouTubeVideo) -> (bool, Path):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.pool, self.sync_download_audio, video)

    def sync_download_video(self,
                            video: YouTubeVideo,
                            required_ext: str = "mp4",
                            required_height: int = 720,
                            fps_limit: int = 30) -> (bool, Path):

        video.generate_link()

        title = self.prepare_title(video.title)
        config = copy.deepcopy(self.__config)
        config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        config["format"] = \
            f"bestvideo[height<={required_height}][ext={required_ext}][fps<={fps_limit}]+bestaudio[ext=m4a]/worst"

        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([video.link])
                logger.info(f"Video downloaded to {self.dir}/{title}.{required_ext}")  # TODO need to be sure of EXT

                return True, Path(f"{self.dir}/{title}.{required_ext}")  # TODO need to be sure of EXT

        except yt_dlp.utils.DownloadError:
            logger.error(f"Exception during audio download for video id: {video.id}")
        except Exception as e:
            logger.error(f"Exception during audio download for video id: {video.id}, {e.__repr__()}")

        return False, Path("")

# SAVING_FOLDER = "saved_files"
#
#
# def make_save_dir() -> Path:
#     absolute_path = Path(__file__).absolute().parent.parent
#     dir_ = Path(f"{absolute_path}/{SAVING_FOLDER}")
#     if not dir_.is_dir():
#         dir_.mkdir()
#         logger.info(f"Saving directory created: {dir_}")
#     logger.info(f"Saving directory set up: {dir_}")
#     return dir_
#
#
# loader = YouTubeLoader(make_save_dir())
#
# loader.sync_download_video(video=YouTubeVideo(
#     id="Zn6scKf7k_0",
#     link="https://www.youtube.com/watch?v=Zn6scKf7k_0&pp=ygUOY2FyIG1hbnVmYWN0dXI%3D",
#     title="iPhone 16/16 Pro Unboxing: End of an Era!",
#     owner_username="123",
#     published_at="123",
#     channel_id="123",
#     kind="123"
# ))
