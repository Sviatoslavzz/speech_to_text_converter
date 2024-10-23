import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from loguru import logger

MINUTE = 60
HOUR = MINUTE * 60
MB = 1024 * 1024
SAVING_FOLDER = "saved_files"


def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API"),
            "TG_TOKEN": os.getenv("TG_TOKEN"),
            "DROPBOX_REFRESH_TOKEN": os.getenv("DROPBOX_REFRESH_TOKEN"),
            "DROPBOX_APP_KEY": os.getenv("DROPBOX_APP_KEY"),
            "DROPBOX_APP_SECRET": os.getenv("DROPBOX_APP_SECRET"), }


def get_save_dir() -> Path:
    absolute_path = Path(__file__).absolute().parent.parent
    dir_ = Path(f"{absolute_path}/{SAVING_FOLDER}")
    if not dir_.is_dir():
        dir_.mkdir()
        logger.info(f"Saving directory created: {dir_}")
    logger.info(f"Saving directory set up: {dir_}")
    return dir_


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


@dataclass(slots=True)
class AppMessage:
    message: dict[str, str] = field(default_factory=dict)
    available_languages: list[str] = field(default_factory=lambda: ["ru"])


@dataclass(slots=True)
class VideoOptions:
    extension: str = "mp4"
    height: int = 720
    fps: int = 30
    language: str = "ru"


@dataclass(slots=True)
class Task:
    id: str
    message: AppMessage = field(default_factory=AppMessage)
    local_path: Path | None = None
    result: bool | None = False
    file_size: int | None = None


@dataclass(slots=True)
class TranscriptionTask(Task):
    origin_path: Path | None = None


@dataclass(slots=True)
class DownloadTask(Task):
    video: YouTubeVideo | None = None
    options: VideoOptions | None = field(default_factory=VideoOptions)
    storage_link: str | None = None


class UserRoute(StatesGroup):
    option = State()  # video / channel / file
    videos = State()  # list of links / channel link
    file = State()
    action = State()  # what to do
