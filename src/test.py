from pprint import pprint
from typing import Any

import yt_dlp
from loguru import logger

from talkushka_service.model.objects import VideoOptions

__config: dict[str, Any] = {
        "quiet": True,
        "socket_timeout": 5,
    }


def get_video_options(link: str) -> list[VideoOptions]:
    """
    Loads and sorts all available video formats with the highest tbr (video bitrate).
    :param link: any video link
    :return: list of video options or empty list
    """
    resolution_dict = {}
    try:
        with yt_dlp.YoutubeDL(__config) as ydl:
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


pprint(get_video_options("https://rutube.ru/video/4ca25c8fd0a124eda20eec3fcafea009/"))
