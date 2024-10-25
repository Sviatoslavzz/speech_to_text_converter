import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from config import DropboxConfig
from executors.process_executor import ProcessExecutor
from storage.dropbox_storage import DropBox
from transcribers.transcriber_worker import TranscriberWorker
from youtube_clients.youtube_api import YouTubeClient
from youtube_clients.youtube_loader import YouTubeLoader

SAVING_FOLDER = "saved_files"


@pytest.fixture
def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API"),
            "TG_TOKEN": os.getenv("TG_TOKEN"),
            "DROPBOX_REFRESH_TOKEN": os.getenv("DROPBOX_REFRESH_TOKEN"),
            "DROPBOX_APP_KEY": os.getenv("DROPBOX_APP_KEY"),
            "DROPBOX_APP_SECRET": os.getenv("DROPBOX_APP_SECRET"),
            "DROPBOX_REFRESH_TOKEN_2": os.getenv("DROPBOX_REFRESH_TOKEN_2"),
            "DROPBOX_APP_KEY_2": os.getenv("DROPBOX_APP_KEY_2"),
            "DROPBOX_APP_SECRET_2": os.getenv("DROPBOX_APP_SECRET_2"),
            }


@pytest.fixture
def saving_path() -> Path:
    absolute_path = Path(__file__).absolute().parent
    saving_path_ = Path(f"{absolute_path}/{SAVING_FOLDER}")
    if not saving_path_.is_dir():
        saving_path_.mkdir()
    return saving_path_


@pytest.fixture
def youtube_api_client(get_env):
    return YouTubeClient(
        get_env.get("YOUTUBE_API")) if not YouTubeClient.get_instance() else YouTubeClient.get_instance()


@pytest.fixture
def youtube_loader(saving_path):
    return YouTubeLoader(saving_path) if not YouTubeLoader.get_instance() else YouTubeLoader.get_instance()


@pytest.fixture
def transcriber_worker():
    return TranscriberWorker().get_instance()


@pytest.fixture
def process_executor(request):
    target = request.param["target"]
    args = request.param.get("args", [])
    kwargs = request.param.get("kwargs", {})

    executor = ProcessExecutor.get_instance()
    if not executor:
        executor = ProcessExecutor(target, *args, **kwargs)
    else:
        executor.reinitialize(target, *args, **kwargs)
    return executor


@pytest.fixture
def dropbox_conf(get_env):
    return [
        DropboxConfig(cls=DropBox,
                      storage_time=40,
                      refresh_token=get_env.get("DROPBOX_REFRESH_TOKEN"),
                      app_key=get_env.get("DROPBOX_APP_KEY"),
                      app_secret=get_env.get("DROPBOX_APP_SECRET")),
        DropboxConfig(cls=DropBox,
                      storage_time=40,
                      refresh_token=get_env.get("DROPBOX_REFRESH_TOKEN_2"),
                      app_key=get_env.get("DROPBOX_APP_KEY_2"),
                      app_secret=get_env.get("DROPBOX_APP_SECRET_2")),
    ]


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
def long_youtube_videos() -> list[str]:
    return [
        "https://www.youtube.com/watch?v=aN-IbSyIw7Q",
        "https://www.youtube.com/watch?v=jxmZOR_-4uI",
        "https://www.youtube.com/watch?v=hUkyLnW6Q30",
        "https://www.youtube.com/watch?v=DZteznd47B4",
        "https://www.youtube.com/watch?v=6jzG-BMannc",
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


@pytest.fixture
def youtube_videos_for_load() -> list[str]:
    return [
        "https://www.youtube.com/shorts/wB1b7m5QfMc",
        "https://www.youtube.com/watch?v=thcEuMDWxoI&pp=ygUSbWVkaXRhdGlvbiBzZWNyZXRz",
        "https://www.youtube.com/watch?v=Vj52NnZC21Y&pp=ygUSbWVkaXRhdGlvbiBzZWNyZXRz",
        "https://www.youtube.com/shorts/A8qWpmdIADQ",
    ]


@pytest.fixture
def youtube_only_shorts() -> list[str]:
    return [
        "https://www.youtube.com/shorts/YnKjN4bMACw",
        "https://www.youtube.com/shorts/3NaK5EX5F9s",
        "https://www.youtube.com/shorts/ms3YxA8rDdQ",
    ]


@pytest.fixture
def youtube_music() -> list[str]:
    return [
        "https://www.youtube.com/watch?v=PHf83VFDw6g&t=3235s",
        "https://www.youtube.com/watch?v=KeaRIJd8Z5E&t=4s",
    ]


@pytest.fixture
def videos_without_subtitles() -> list[str]:
    return [
        "https://www.youtube.com/shorts/ixaKx5GKFJM",
        "https://www.youtube.com/shorts/Sgfc-5C_76k",
        "https://www.youtube.com/shorts/dNTo51QSO6g",
    ]


@pytest.fixture
def files():
    return [
        "test_1.mp4",
        "test_2.mp4",
        "test_3.mp4",
        "test_4.mp4",
        "test_5.mp4",
        "test_6.mp4",
        "test_7.mp4",
        "test_8.mp4",
    ]
