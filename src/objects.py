from dataclasses import dataclass
from enum import Enum


class DownloadOptions(Enum):
    TEXT = 1
    AUDIO = 2
    VIDEO = 3
    EXIT = 4


@dataclass
class YouTubeVideo:
    id: str
    link: str | None
    title: str
    owner_username: str
    published_at: str
    channel_id: str
    kind: str

    @staticmethod
    def generate_link(video_id: str) -> str:
        return "https://www.youtube.com/watch?v=" + video_id
