import asyncio

import pytest

from objects import TranscriptionTask


@pytest.mark.skip(reason="Only manual testing, files required")
@pytest.mark.asyncio
async def test_transciber_worker_async(saving_path, files, transcriber_worker):
    worker = transcriber_worker
    tasks = [asyncio.create_task(worker.transcribe(TranscriptionTask(origin_path=saving_path / filename))) for filename
             in files]
    results: list[TranscriptionTask] = await asyncio.gather(*tasks)
    for task in results:
        assert task.result is True
        task.local_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_e2e(saving_path, videos_without_subtitles, youtube_loader, transcriber_worker, youtube_api_client):
    for link in videos_without_subtitles:
        video = await youtube_api_client.get_video_by_link(link)
        state, path_ = await youtube_loader.download_audio(video)
        assert state is True
        task: TranscriptionTask = await transcriber_worker.transcribe(TranscriptionTask(origin_path=path_))
        assert task.result is True
        task.local_path.unlink(missing_ok=True)
        task.origin_path.unlink(missing_ok=True)


async def example_task(youtube_api_client, youtube_loader, transcriber_worker, link: str):
    video = await youtube_api_client.get_video_by_link(link)
    state, path_ = await youtube_loader.download_audio(video)
    assert state is True
    result_task: TranscriptionTask = await transcriber_worker.transcribe(TranscriptionTask(origin_path=path_))
    assert result_task.result is True
    result_task.origin_path.unlink(missing_ok=True)
    result_task.local_path.unlink(missing_ok=True)


@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_e2e_async(saving_path, videos_without_subtitles, youtube_loader, transcriber_worker, youtube_api_client):
    tasks = [
        asyncio.create_task(example_task(youtube_api_client, youtube_loader, transcriber_worker, link)) \
        for link in videos_without_subtitles
    ]
    await asyncio.gather(*tasks)
