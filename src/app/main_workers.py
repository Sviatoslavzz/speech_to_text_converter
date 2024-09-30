import os

from dotenv import load_dotenv

from objects import YouTubeVideo
from youtube_workers.youtube_api import YouTubeClient


def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API")}

def validate_links() -> list[YouTubeVideo | None]:
    pass