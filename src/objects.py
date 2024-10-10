import os
from dataclasses import dataclass
from enum import Enum

from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

MB = 1024 * 1024

def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API"),
            "TOKEN": os.getenv("TOKEN"),
            "DROPBOX_REFRESH_TOKEN": os.getenv("DROPBOX_REFRESH_TOKEN"),
            "DROPBOX_APP_KEY": os.getenv("DROPBOX_APP_KEY"),
            "DROPBOX_APP_SECRET": os.getenv("DROPBOX_APP_SECRET"), }


class DownloadOptions(Enum):
    TEXT = 1
    AUDIO = 2
    VIDEO = 3
    EXIT = 4


@dataclass(slots=True)
class YouTubeVideo:
    id: str
    link: str | None
    title: str
    owner_username: str
    published_at: str
    channel_id: str
    kind: str

    def generate_link(self) -> str:
        self.link = f"https://www.youtube.com/watch?v={self.id}"
        return self.link


class UserRoute(StatesGroup):
    option = State()  # video / channel / file
    videos = State()  # list of links / channel link
    file = State()
    action = State()  # what to do
