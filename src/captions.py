import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi

from yt_dlp_loader import YouTubeLoader


async def get_caption_by_link(directory: Path, link: str) -> bool:
    """
    Asynchronously loads YouTube video captions in the preferred language if exist
    :param directory: save directory path
    :param link: YouTube video link
    :return: True in case of success, False in case of failure
    """
    # TODO придумать пре валидацию линки и вынести отсюда
    # TODO по сути эта функция работает с ID
    if "v=" in link:
        video_id = link.split("v=")[1]
    elif "live/" in link:
        video_id = link.split("live/")[1]
    else:
        return False

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=20) as executor:
        title, valid = await loop.run_in_executor(
            executor, YouTubeLoader.get_title, link
        )  # TODO забирать название из гугл API
        if not valid:
            logger.warning(f"Unable to get video title for {link}")

            return False
        try:
            transcript = await loop.run_in_executor(
                executor, YouTubeTranscriptApi.get_transcript, video_id, ["ru", "en"]
            )
            target_path = (directory / title).with_suffix(".txt")
            with target_path.open(mode="w") as file:
                for entry in transcript:
                    file.write(entry["text"].replace("\n", " ") + " ")
            logger.info(f"Captions saved to {target_path}")

            return True
        except Exception as e:
            logger.warning(f"An exception occurred: {e!s}")

            return False
