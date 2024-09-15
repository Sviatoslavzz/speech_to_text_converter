import asyncio

import pytest
from dotenv import load_dotenv
import os

from sympy.physics.units import volts

from src.youtube_api import YouTubeClient


@pytest.fixture
def get_env() -> dict[str, str]:
    load_dotenv()
    env_dict = {"YouTube_API": os.getenv("YouTube_API")}
    return env_dict


@pytest.fixture
def youtube_api_client(get_env):
    return YouTubeClient(get_env.get("YouTube_API"))


@pytest.fixture
def correct_channels_list() -> list[dict[str, str]]:
    return [
        {
            "link": "https://www.youtube.com/@Web3nity",
            "id": "UCuaYG7fdQ-4myL_CVtvwNHQ"
        },
        {
            "link": "https://www.youtube.com/channel/UCuaYG7fdQ-4myL_CVtvwNHQ",
            "id": "UCuaYG7fdQ-4myL_CVtvwNHQ"
        },
        {
            "link": "https://www.youtube.com/@Gilevich_Sergey",
            "id": "UCNAlb9eRKqyO4-TBO7xMuug"
        },
        {
            "link": "https://www.youtube.com/channel/UCNAlb9eRKqyO4-TBO7xMuug",
            "id": "UCNAlb9eRKqyO4-TBO7xMuug"
        }
    ]


@pytest.fixture
def incorrect_channels_list() -> list[dict[str, str]]:
    return [
        {
            "link": "https://www.youtube.com/@1251251251251!",
            "id": None
        },
        {
            "link": "https://www.youtube.com/channel/UCuaYG7fdQ-4myL_CVtvwNHQ2334",
            "id": None
        },
        {
            "link": "123456",
            "id": None
        },
        {
            "link": "https://www.youtube.com",
            "id": None
        }
    ]


@pytest.mark.asyncio
async def test_get_channel_id(youtube_api_client, correct_channels_list):
    await asyncio.sleep(1)
    ytb = youtube_api_client

    for channel in correct_channels_list:
        channel_id = await ytb.get_channel_id_by_link(channel.get("link"))
        assert channel_id == channel.get("id")


@pytest.mark.asyncio
async def test_get_channel_id_wrong(youtube_api_client, incorrect_channels_list):
    await asyncio.sleep(1)
    ytb = youtube_api_client

    for channel in incorrect_channels_list:
        channel_id = await ytb.get_channel_id_by_link(channel.get("link"))
        assert channel_id is None

@pytest.mark.asyncio
async def test_get_channels_videos(youtube_api_client, correct_channels_list):
    await asyncio.sleep(1)
    ytb = youtube_api_client

    for i in range(0, len(correct_channels_list), 2):
        amount, videos = await ytb.get_channel_videos(correct_channels_list[i].get("id"))
        assert amount == len(videos)

@pytest.mark.asyncio
async def test_async_speed(youtube_api_client, correct_channels_list, incorrect_channels_list):
    await asyncio.sleep(1)

    ytb = youtube_api_client

    tasks = [asyncio.create_task(ytb.get_channel_id_by_link(channel.get("link"))) for channel in correct_channels_list]
    tasks.extend(
        [asyncio.create_task(ytb.get_channel_id_by_link(channel.get("link"))) for channel in incorrect_channels_list]
    )

    results = await asyncio.gather(*tasks)
    assert results is not None
