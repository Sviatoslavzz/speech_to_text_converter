from pathlib import Path

import pytest
import os
from dotenv import load_dotenv

from youtube_api import YouTubeClient
from yt_dlp_loader import YouTubeLoader

SAVING_FOLDER = "saved_files"


@pytest.fixture
def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API")}


@pytest.fixture
def saving_path() -> Path:
    absolute_path = Path(__file__).absolute().parent
    saving_path_ = Path(f"{absolute_path}/{SAVING_FOLDER}")
    if not saving_path_.is_dir():
        saving_path_.mkdir()
    return saving_path_


@pytest.fixture
def youtube_api_client(get_env):
    return YouTubeClient(get_env.get("YOUTUBE_API"))


@pytest.fixture
def youtube_loader(saving_path):
    return YouTubeLoader(saving_path)


@pytest.fixture
def correct_channels_list() -> list[dict[str, str]]:
    return [
        {"link": "https://www.youtube.com/@Web3nity", "id": "UCuaYG7fdQ-4myL_CVtvwNHQ"},
        {"link": "https://www.youtube.com/channel/UCuaYG7fdQ-4myL_CVtvwNHQ", "id": "UCuaYG7fdQ-4myL_CVtvwNHQ"},
        {"link": "https://www.youtube.com/@Gilevich_Sergey", "id": "UCNAlb9eRKqyO4-TBO7xMuug"},
        {"link": "https://www.youtube.com/channel/UCNAlb9eRKqyO4-TBO7xMuug", "id": "UCNAlb9eRKqyO4-TBO7xMuug"},
    ]


@pytest.fixture
def incorrect_channels_list() -> list[dict[str, str]]:
    return [
        {"link": "https://www.youtube.com/@1251251251251!", "id": None},
        {"link": "https://www.youtube.com/channel/UCuaYG7fdQ-4myL_CVtvwNHQ2334", "id": None},
        {"link": "123456", "id": None},
        {"link": "https://www.youtube.com", "id": None},
    ]


@pytest.fixture
def youtube_videos() -> list[str]:
    return [
        "https://www.youtube.com/watch?v=Zn6scKf7k_0&pp=ygUOY2FyIG1hbnVmYWN0dXI%3D",
        "https://www.youtube.com/watch?v=mCMbPsfn_54",
        "https://www.youtube.com/watch?v=3qkT0NpHrCQ&pp=ygUOY2FyIG1hbnVmYWN0dXI%3D",
        "https://www.youtube.com/shorts/jcVHxxVWazg",
        "https://www.youtube.com/live/GN2iEGZe16A",
    ]


@pytest.fixture
def youtube_videos_wrong() -> list[str]:
    return [
        "https://www.youtube.com/watch?vZn6scKf7k_0&pp=ygUOY2FyIG1hbnVmYWN0dXI%3D",
        "https://www.youtube.com/watch?=mCMbPsfn_54",
        "https://www.youtube.com/watch?v=3qkT&&&&0NpHrCQ&pp=ygUOY2FyIG1hbnVmYWN0dXI%3D",
        "https://www.youtube.com/shorts/jcVHxx&VWazg",
        "https://www.youtube.com/live/",
        "https://www.google.com/",
    ]
