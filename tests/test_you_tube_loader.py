import asyncio

import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_title_preparation(youtube_loader, youtube_api_client, youtube_videos):
    for link in youtube_videos:
        video = await youtube_api_client.form_video_from_link(link)
        title = youtube_loader.prepare_title(video.title)
        for letter in title:
            assert letter.isalpha() or letter == "_"


@pytest.mark.asyncio
async def test_download_audio_concurrent(youtube_loader, youtube_api_client, youtube_videos):
    await asyncio.sleep(1)
    tasks = []
    client = youtube_loader
    for link in youtube_videos:
        video = await youtube_api_client.form_video_from_link(link)
        tasks.append(asyncio.create_task(client.download_audio(video)))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            pytest.fail(f"Task failed: {result}")

        state, result_path = result
        assert state is True
        assert isinstance(result_path, Path)
        assert result_path.suffix == ".mp3"
        result_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_download_audio(youtube_loader, youtube_api_client, youtube_videos):
    await asyncio.sleep(1)
    client = youtube_loader
    for link in youtube_videos:
        video = await youtube_api_client.form_video_from_link(link)
        state, result_path = await client.download_audio(video)
        assert state is True
        assert isinstance(result_path, Path)
        assert result_path.suffix == ".mp3"
        result_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_download_video(youtube_loader, youtube_api_client, youtube_videos):
    await asyncio.sleep(1)
    client = youtube_loader
    for link in youtube_videos:
        video = await youtube_api_client.form_video_from_link(link)
        state, result_path = client.sync_download_video(video, required_height=240)
        assert state is True
        assert isinstance(result_path, Path)
        assert result_path.suffix == ".mp4"
        result_path.unlink(missing_ok=True)
        # break
