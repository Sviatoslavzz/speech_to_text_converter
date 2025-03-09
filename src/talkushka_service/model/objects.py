from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

MINUTE = 60
HOUR = MINUTE * 60
MB = 1024 * 1024


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
class DownloadTask:
    id: str
    video: YouTubeVideo
    message: dict[str, str] = field(default_factory=dict)
    options: VideoOptions = field(default_factory=VideoOptions)
    local_path: Path | None = None
    result: bool | None = False
    file_size: int | None = None
    storage_link: str | None = None
