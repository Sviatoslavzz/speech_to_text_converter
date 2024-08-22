import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from loguru import logger

import yt_dlp
from os import remove


class YtLoader:
    _audio_config = {
        'format': 'bestaudio/best',  # the best audio quality available
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # Quality in kbps (e.g., 192)
        }],
        'outtmpl': '',  # Output filename template
        'quiet': True,
    }
    _video_config = {
        'format': 'bestvideo+bestaudio/best',  # the best video and audio quality available
        'outtmpl': '',
        'quiet': True,
    }

    def __init__(self, directory: Path):
        self.dir = directory
        self._title = "example"
        logger.info(f"Yt_loader init")

    def __del__(self):
        if self._title.endswith(".webm"):
            remove(f"{self.dir}/{self._title}")

    def remove_audio_file(self):
        if self._title.endswith(".mp3"):
            remove(f"{self.dir}/{self._title}")

    @classmethod
    def get_title(cls, link_) -> (str, bool):
        try:
            with yt_dlp.YoutubeDL(cls._audio_config) as ydl:
                info_dict = ydl.extract_info(link_, download=False)
                cls._title = info_dict.get('title', None)
                cls._title = cls._prepare_title(cls._title)
                return cls._title, True
        except yt_dlp.utils.DownloadError:
            return cls._title, False

    @staticmethod
    def _prepare_title(title_) -> str:
        title_ = title_.encode('utf-8').decode('utf-8').rstrip(' .')
        title_ = title_.lower()
        replacements = {
            ',': ' ',
            '!': ' ',
            '?': ' ',
            "'": ' ',
            "/": '',
            ' ': '_',
            '\\': '',
            '|': '',
            '.': '_',
        }
        for old, new in replacements.items():
            title_ = title_.replace(old, new)
        return title_

    def download_audio(self, link_) -> (str, bool):
        self._title, is_valid = self.get_title(link_)
        if is_valid:
            self._audio_config['outtmpl'] = f'{self.dir}/{self._title}.%(ext)s'
            try:
                with yt_dlp.YoutubeDL(self._audio_config) as ydl:
                    ydl.download([link_])
                    self._title = self._title.replace('.webm', '')
                    # self._title = self._title + ".mp3"  # TODO title validation required
                    return f'{self._title}.mp3', True
            except yt_dlp.utils.DownloadError:
                print(f'An error occurred while downloading audio for: "{link_}"')
                self._title = self._title + ".webm"
                return "", False
        else:
            print(f'provided link is not valid: "{link_}"')
            return "", False

    async def async_download_audio(self, link_) -> (str, bool):
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
            if fmt.get('format_note') == quality:
                format_code = f"{fmt['format_id']}+bestaudio/best"
                break

        if not format_code:
            format_code = 'bestvideo+bestaudio/best'

        self._video_config['format'] = format_code
        self._video_config['outtmpl'] = f'{self.dir}/{self._title}.%(ext)s'
        try:
            with yt_dlp.YoutubeDL(self._video_config) as ydl:
                ydl.download([link_])
                self._title = self._title + ".mp4"
                return f'{self._title}', True
        except yt_dlp.utils.DownloadError:
            print(f'An error occurred while downloading video for: "{link_}"')
            self._title = self._title + ".webm"
            return "", False

    def _list_available_formats(self, link_):
        try:
            with yt_dlp.YoutubeDL(self._video_config) as ydl:
                formats = ydl.extract_info(link_, download=False)['formats']
                return formats
        except yt_dlp.utils.DownloadError:
            return []
