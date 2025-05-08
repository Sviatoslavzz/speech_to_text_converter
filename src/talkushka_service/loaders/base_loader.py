from typing import Any

import yt_dlp
from loguru import logger

from talkushka_service.model.objects import VideoOptions


class BaseLoader:

    __config: dict[str, Any] = {
        "quiet": True,
        "socket_timeout": 5,
    }
    #
    # def __init__(self, directory: Path, heavy_pool_size: int, light_pool_size: int, proxy: str | None = None):
    #     self.dir = directory
    #     if proxy:
    #         self.__config["proxy"] = proxy
    #
    #     logger.debug("{cls} : initialized")

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

    def get_video_options(self, link: str) -> list[VideoOptions]:
        """
        Loads and sorts all available video formats with the highest tbr (avg video bitrate).
        :param link: any video link
        :return: list of video options or empty list
        """
        resolution_dict = {}
        try:
            with yt_dlp.YoutubeDL(self.__config) as ydl:
                info_dict = ydl.extract_info(link, download=False)
                formats = info_dict.get("formats", [])
                for f in formats:
                    if (
                            f.get("fps")
                            and f.get("width")
                            and f.get("height")
                            and f.get("ext") == "mp4"
                            and f.get("tbr")
                    ):
                        cur_key = VideoOptions(width=f.get("width"), height=f.get("height"), fps=f.get("fps"))
                        if resolution_dict.get(cur_key) and resolution_dict[cur_key] < f.get("tbr"):
                            resolution_dict[cur_key] = f.get("tbr")
                        else:
                            resolution_dict[cur_key] = f.get("tbr")
                logger.debug("Successfully got options for video {link}", link=link)
        except Exception:
            logger.exception("Exception during extracting video info")

        return list(resolution_dict)
