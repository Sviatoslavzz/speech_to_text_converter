import asyncio
import time

import pytest

from objects import DownloadTask, VideoOptions, YouTubeVideo
from storage.storage_worker import StorageWorker, storage_worker_as_target


def test_launch(dropbox_conf):
    sw = StorageWorker.get_instance()
    if not sw:
        sw = StorageWorker(dropbox_conf)
    if not sw.is_connected():
        sw.connect_storages()
    time.sleep(2)
    sw.stop_storages()


@pytest.mark.asyncio
async def test_update_space(dropbox_conf):
    sw = StorageWorker.get_instance()
    if not sw:
        sw = StorageWorker(dropbox_conf)
    if not sw.is_connected():
        sw.connect_storages()
    await sw.update_space()
    await asyncio.sleep(2)
    sw.stop_storages()


@pytest.mark.asyncio
async def test_worker_as_target_e2e(youtube_api_client, youtube_loader, youtube_videos_for_load, dropbox_conf):
    sw = StorageWorker.get_instance()
    if not sw:
        sw = StorageWorker(dropbox_conf)
    if not sw.is_connected():
        sw.connect_storages()

    spaces = await sw.update_space()

    for link in youtube_videos_for_load:
        video: YouTubeVideo = await youtube_api_client.get_video_by_id(youtube_api_client.get_video_id(link))
        task: DownloadTask = DownloadTask(video=video, id=video.id, options=VideoOptions())
        task = await youtube_loader.download_video(task)
        task = await storage_worker_as_target(task)
        assert task.result
        assert "dropbox" in task.storage_link

    cur_time = time.time()

    while time.time() < cur_time + 90:
        await storage_worker_as_target()
        await asyncio.sleep(1)

    assert spaces == await sw.update_space()

    if sw and sw.is_connected():
        sw.stop_storages()
