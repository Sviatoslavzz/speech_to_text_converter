import asyncio
from pathlib import Path

import pytest

from objects import DownloadTask, VideoOptions


@pytest.mark.asyncio
async def test_title_preparation(youtube_loader, youtube_api_client, youtube_videos):
    for link in youtube_videos:
        video = await youtube_api_client.get_video_by_link(link)
        title = youtube_loader.prepare_title(video.title)
        for letter in title:
            assert letter.isalpha() or letter == "_" or letter.isdigit()


@pytest.mark.asyncio
async def test_download_audio(youtube_loader, youtube_api_client, youtube_videos_for_load):
    await asyncio.sleep(1)
    client = youtube_loader
    for link in youtube_videos_for_load:
        video = await youtube_api_client.get_video_by_link(link)
        task = await client.download_audio(DownloadTask(id=video.id, video=video))
        assert task.result
        assert isinstance(task.local_path, Path)
        assert task.local_path.suffix == ".mp3"
        task.local_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_download_audio_async(youtube_loader, youtube_api_client, youtube_videos_for_load):
    await asyncio.sleep(1)
    tasks = []
    client = youtube_loader
    for link in youtube_videos_for_load:
        video = await youtube_api_client.get_video_by_link(link)
        task = DownloadTask(id=video.id, video=video)
        tasks.append(asyncio.create_task(client.download_audio(task)))

    results = await asyncio.gather(*tasks)
    for task in results:
        assert task.result
        assert task.local_path is not None and isinstance(task.local_path, Path)
        assert task.local_path.suffix == ".mp3"
        task.local_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_download_video(youtube_loader, youtube_api_client, youtube_videos_for_load):
    await asyncio.sleep(1)
    client = youtube_loader
    for link in youtube_videos_for_load:
        video = await youtube_api_client.get_video_by_link(link)
        task = await client.download_video(DownloadTask(id=video.id, video=video, options=VideoOptions(height=480)))
        assert task.result is True
        assert isinstance(task.local_path, Path)
        assert task.local_path.suffix == ".mp4"
        task.local_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_download_video_async(youtube_loader, youtube_api_client, youtube_videos_for_load):
    await asyncio.sleep(1)
    tasks = []
    client = youtube_loader
    for link in youtube_videos_for_load:
        video = await youtube_api_client.get_video_by_link(link)
        tasks.append(asyncio.create_task(client.download_video(DownloadTask(id=video.id, video=video))))

    results: list[DownloadTask] = await asyncio.gather(*tasks, return_exceptions=True)
    for task in results:
        assert task.result
        assert isinstance(task.local_path, Path)
        assert task.local_path.suffix == ".mp4"
        task.local_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_get_captions(youtube_loader, youtube_api_client, youtube_videos, youtube_only_shorts):
    for link in youtube_videos + youtube_only_shorts:
        video = await youtube_api_client.get_video_by_link(link)
        res_task: DownloadTask = await youtube_loader.get_captions(DownloadTask(id=video.id, video=video))
        assert res_task.result
        with res_task.local_path.open(mode="r", encoding="utf-8") as file:
            assert len(file.read()) > 0
        res_task.local_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_get_captions_wrong(youtube_loader, youtube_api_client, youtube_music):
    for link in youtube_music:
        video = await youtube_api_client.get_video_by_link(link)
        res_task: DownloadTask = await youtube_loader.get_captions(DownloadTask(id=video.id, video=video))
        assert not res_task.result


@pytest.mark.asyncio
async def test_get_captions_async(youtube_loader, youtube_api_client, youtube_videos, youtube_only_shorts):
    tasks = []
    for link in youtube_videos + youtube_only_shorts:
        video = await youtube_api_client.get_video_by_link(link)
        tasks.append(asyncio.create_task(youtube_loader.get_captions(DownloadTask(id=video.id, video=video))))

    results = await asyncio.gather(*tasks)
    for task in results:
        assert task.result is True
        with task.local_path.open(mode="r", encoding="utf-8") as file:
            assert len(file.read()) > 0
        task.local_path.unlink(missing_ok=True)

@pytest.mark.skip(reason="Requires manually change the pools size ~4 ~4")
@pytest.mark.asyncio
async def test_full_threads_capacity(youtube_loader, youtube_api_client, long_youtube_videos, youtube_videos):
    """
    Test for checking the actual work of 2 separated pool executors for video and caption loading
    """
    load_tasks = []
    for link in long_youtube_videos:
        video = await youtube_api_client.get_video_by_link(link)
        load_tasks.append(asyncio.create_task(youtube_loader.download_video(DownloadTask(id=video.id, video=video))))

    for link in youtube_videos:
        video = await youtube_api_client.get_video_by_link(link)
        load_tasks.append(asyncio.create_task(youtube_loader.get_captions(DownloadTask(id=video.id, video=video))))

    results = await asyncio.gather(*load_tasks)
    for task in results:
        assert task.result is True
        task.local_path.unlink(missing_ok=True)
