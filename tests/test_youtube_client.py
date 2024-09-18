import asyncio
import pytest

from objects import YouTubeVideo
from youtube_api import YouTubeClient


@pytest.mark.asyncio
async def test_get_channel_id(youtube_api_client, correct_channels_list):
    await asyncio.sleep(1)

    for channel in correct_channels_list:
        channel_id = await youtube_api_client.get_channel_id_by_link(channel.get("link"))
        assert channel_id == channel.get("id")


@pytest.mark.asyncio
async def test_get_channel_id_wrong(youtube_api_client, incorrect_channels_list):
    await asyncio.sleep(1)

    for channel in incorrect_channels_list:
        channel_id = await youtube_api_client.get_channel_id_by_link(channel.get("link"))
        assert channel_id is None


@pytest.mark.asyncio
async def test_get_channels_videos(youtube_api_client, correct_channels_list):
    await asyncio.sleep(1)

    for i in range(0, len(correct_channels_list), 2):
        amount, videos = await youtube_api_client.get_channel_videos(correct_channels_list[i].get("id"))
        assert amount == len(videos)


@pytest.mark.asyncio
async def test_async_speed(youtube_api_client, correct_channels_list, incorrect_channels_list):
    await asyncio.sleep(1)

    tasks = [asyncio.create_task(youtube_api_client.get_channel_id_by_link(channel.get("link"))) for channel in correct_channels_list]
    tasks.extend(
        [asyncio.create_task(youtube_api_client.get_channel_id_by_link(channel.get("link"))) for channel in incorrect_channels_list]
    )

    results = await asyncio.gather(*tasks)
    assert results is not None


@pytest.mark.asyncio
async def test_form_video_from_link(youtube_api_client, youtube_videos):
    await asyncio.sleep(1)

    for link in youtube_videos:
        result = await youtube_api_client.form_video_from_link(link)
        assert isinstance(result, YouTubeVideo)
        assert result.generate_link() is not None


@pytest.mark.asyncio
async def test_form_video_from_link_wrong(youtube_api_client, youtube_videos_wrong):
    await asyncio.sleep(1)

    for link in youtube_videos_wrong:
        result = await youtube_api_client.form_video_from_link(link)
        assert not result
