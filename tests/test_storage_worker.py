import asyncio
import time

import pytest

from objects import DownloadTask, YouTubeVideo, VideoOptions
from storage.storage_worker import StorageWorker, storage_worker_as_target


def test_launch():
    sw = StorageWorker.get_instance()
    if not sw:
        sw = StorageWorker(storage_time=120)
    if not sw.is_connected():
        sw.connect_storages()
    time.sleep(2)
    sw.stop_storages()


@pytest.mark.asyncio
async def test_update_space():
    sw = StorageWorker.get_instance()
    if not sw:
        sw = StorageWorker(storage_time=120)
    if not sw.is_connected():
        sw.connect_storages()
    await sw.update_space()
    await asyncio.sleep(2)
    sw.stop_storages()


@pytest.mark.skip(reason="Only manual testing, requires manual limiting for storage timers")
@pytest.mark.asyncio
async def test_worker_as_target_e2e(youtube_api_client, youtube_loader, youtube_videos_for_load):
    for link in youtube_videos_for_load:
        video: YouTubeVideo = await youtube_api_client.get_video_by_link(link)
        task: DownloadTask = DownloadTask(video=video, id=video.id, options=VideoOptions())
        task = await youtube_loader.download_video(task)
        print(f"path = {task.local_path}")
        print(f"result = {task.result}")
        print(f"file size = {task.file_size}")

        task = await storage_worker_as_target(task)
        print(task.storage_link)

    cur_time = time.time()

    while time.time() < cur_time + 150:
        await storage_worker_as_target()
        await asyncio.sleep(1)

    sw = StorageWorker.get_instance()
    if sw and sw.is_connected():
        sw.stop_storages()
