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
SERVER = "telegram"  # "telegram" "local"

def get_env() -> dict[str, str]:
    load_dotenv()
    return {
        "YOUTUBE_API": os.getenv("YOUTUBE_API"),
        "TG_BOT_TOKEN": os.getenv("TG_BOT_TOKEN"),
        "LOCAL_BOT_TOKEN": os.getenv("LOCAL_BOT_TOKEN"),
        "DROPBOX_REFRESH_TOKEN": os.getenv("DROPBOX_REFRESH_TOKEN"),
        "DROPBOX_APP_KEY": os.getenv("DROPBOX_APP_KEY"),
        "DROPBOX_APP_SECRET": os.getenv("DROPBOX_APP_SECRET"),
        "DROPBOX_REFRESH_TOKEN_2": os.getenv("DROPBOX_REFRESH_TOKEN_2"),
        "DROPBOX_APP_KEY_2": os.getenv("DROPBOX_APP_KEY_2"),
        "DROPBOX_APP_SECRET_2": os.getenv("DROPBOX_APP_SECRET_2"),
    }


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


@dataclass(slots=True, frozen=True)
class VideoOptions:
    extension: str = "mp4"
    width: int = 1280
    height: int = 720
    fps: int = 30
    language: str = "ru"

    def __str__(self):
        return f"{self.width}x{self.height}:{self.fps}.{self.extension}"


@dataclass(slots=True)
class TranscriptionTask:
    id: str
    message: AppMessage = field(default_factory=AppMessage)
    local_path: Path | None = None
    result: bool | None = False
    file_size: int | None = None
    origin_path: Path | None = None


@dataclass(slots=True)
class DownloadTask:
    id: str
    video: YouTubeVideo
    message: AppMessage = field(default_factory=AppMessage)
    options: VideoOptions = field(default_factory=VideoOptions)
    local_path: Path | None = None
    result: bool | None = False
    file_size: int | None = None
    storage_link: str | None = None


class UserRoute(StatesGroup):
    """user route states"""
    option = State()  # str : video | channel | file
    videos = State()  # [links] | channel link
    file = State()
    action = State()  # str : download_video | download_audio | download_text
    load_options = State()  # [VideoOptions] | str(width:height:fps)
    single_video_options = State()
    multi_video_options = State()
