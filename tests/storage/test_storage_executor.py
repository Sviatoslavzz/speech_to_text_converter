import asyncio

import pytest

from executors.storage_executor import StorageExecutor
from objects import DownloadTask, VideoOptions, YouTubeVideo
from workers import run_storage_executor


@pytest.mark.skip(reason="Requires changing storage timeout ~45 recommended")
@pytest.mark.asyncio
async def test_e2e_with_storage(youtube_api_client, youtube_loader, youtube_videos_for_load):
    tasks = []
    for link in youtube_videos_for_load:
        video: YouTubeVideo = await youtube_api_client.get_video_by_id(youtube_api_client.get_video_id(link))
        task: DownloadTask = DownloadTask(video=video, id=video.id, options=VideoOptions())
        task = await youtube_loader.download_video(task)
        tasks.append(task)

    results = await run_storage_executor(tasks)

    assert len(results) == len(tasks)

    for result in results:
        assert result.result is True
        assert "dropbox" in result.storage_link
        assert result.file_size is not None

    # wait till storage clears
    await asyncio.sleep(70)

    executor = StorageExecutor.get_instance()
    executor.stop()
    assert not executor.is_alive()
