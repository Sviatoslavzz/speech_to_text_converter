import asyncio
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

    _video_config = {
        "format": "bestvideo+bestaudio/best",  # the best video and audio quality available
        "outtmpl": "",
        "quiet": True,
    }

    def __init__(self, directory: Path):
        self.dir = directory
        logger.info("YouTubeLoader instance initialized")

    # def __del__(self):
    #     if self._title.endswith(".webm"):
    #         (self.dir / self._title).unlink(missing_ok=True)

    def remove_audio_file(self) -> None:
        if self._title.endswith(".mp3"):
            (self.dir / self._title).unlink(missing_ok=True)

    @staticmethod
    def prepare_title(title: str) -> str:
        # title = title.encode("utf-8").decode("utf-8")
        new_title = ""
        flag_fill = True
        for letter in title:
            if letter.isalpha():
                new_title += letter
                flag_fill = True
            elif flag_fill:
                new_title += "_"
                flag_fill = False

        return new_title.strip("_").lower()

    def download_audio(self, video: YouTubeVideo) -> (bool, str):
        """
        Downloads audio from the YouTube video.
        :param video: YouTubeVideo instance with the checked video meta
        :return:
        """
        title = self.prepare_title(video.title)
        ext = self._audio_config["postprocessors"][0]["preferredcodec"]
        self._audio_config["outtmpl"] = f"{self.dir}/{title}.%(ext)s"
        try:
            with yt_dlp.YoutubeDL(self._audio_config) as ydl:
                ydl.download([video.generate_link()])
                logger.info(f"Audio downloaded to {self.dir}/{title}.{ext}")
                return True, f"{self.dir}/{title}.{ext}"
        except yt_dlp.utils.DownloadError:
            logger.error(f"Exception during audio download for video id: {video.id}")
            return False, ""

    async def async_download_audio(self, link_: str) -> (str, bool):
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=20) as pool:
            return await loop.run_in_executor(pool, self.download_audio, link_)

    def download_video(self, link_: str, quality: str = "720p") -> (str, bool):
        # TODO как будто бы не видит дефолтные 720p
        self._title, is_valid = self.get_title(link_)
        if not is_valid:
            print(f'provided link is not valid: "{link_}"')
            return "", False

        available_formats = self._list_available_formats(link_)
        format_code = None

        # Find the format code for the desired quality
        for fmt in available_formats:
            if fmt.get("format_note") == quality:
                format_code = f"{fmt['format_id']}+bestaudio/best"
                break

        if not format_code:
            format_code = "bestvideo+bestaudio/best"

        self._video_config["format"] = format_code
        self._video_config["outtmpl"] = f"{self.dir}/{self._title}.%(ext)s"
        try:
            with yt_dlp.YoutubeDL(self._video_config) as ydl:
                ydl.download([link_])
                self._title = self._title + ".mp4"
                return f"{self._title}", True
        except yt_dlp.utils.DownloadError:
            print(f'An error occurred while downloading video for: "{link_}"')
            self._title = self._title + ".webm"
            return "", False

    def _list_available_formats(self, link_: str) -> list:
        try:
            with yt_dlp.YoutubeDL(self._video_config) as ydl:
                return ydl.extract_info(link_, download=False)["formats"]
        except yt_dlp.utils.DownloadError:
            return []
