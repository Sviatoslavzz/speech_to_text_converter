from youtube_transcript_api import YouTubeTranscriptApi

from yt_dlp_loader import Yt_loader
import asyncio
from concurrent.futures import ThreadPoolExecutor


async def get_caption_by_link(directory: str, link: str) -> bool:
    # TODO придумать пре валидацию линки
    if "v=" in link:
        video_id = link.split("v=")[1]
    elif "live/" in link:
        video_id = link.split("live/")[1]
    else:
        return False

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=20) as executor:
        title, valid = await loop.run_in_executor(executor, Yt_loader.get_title, link)
        if not valid:
            print(f"Unable to get video title for {link}")

            return False
        try:
            transcript = await loop.run_in_executor(executor, YouTubeTranscriptApi.get_transcript, video_id,
                                                    ['ru', 'en'])
            with open(f'{directory}/{title}.txt', "w") as file:
                for entry in transcript:
                    file.write(entry['text'].replace('\n', ' ') + ' ')

            return True
        except Exception as e:
            print(f"An error occurred: {str(e)}")

            return False
