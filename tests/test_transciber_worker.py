import asyncio

import pytest


@pytest.mark.skip(reason="Only manual testing, files required")
@pytest.mark.asyncio
async def test_transciber_worker_async(saving_path, files, transcriber_worker):
    worker = transcriber_worker
    tasks = [asyncio.create_task(worker.transcribe(saving_path / filename) for filename in files)]
    results = await asyncio.gather(*tasks)
    for result in results:
        assert result is True


@pytest.mark.asyncio
async def test_e2e(saving_path, videos_without_subtitles, youtube_loader, transcriber_worker, youtube_api_client):
    for link in videos_without_subtitles:
        video = await youtube_api_client.get_video_by_link(link)
        state, path_ = await youtube_loader.download_audio(video)
        assert state is True
        result, path_ = await transcriber_worker.transcribe(path_)
        assert result is True
        path_.unlink(missing_ok=True)
        path_.with_suffix(".txt").unlink(missing_ok=True)


async def example_task(youtube_api_client, youtube_loader, transcriber_worker, link: str):
    video = await youtube_api_client.get_video_by_link(link)
    state, path_ = await youtube_loader.download_audio(video)
    assert state is True
    result, path_ = await transcriber_worker.transcribe(path_)
    assert result is True
    path_.unlink(missing_ok=True)
    path_.with_suffix(".txt").unlink(missing_ok=True)


@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_e2e_async(saving_path, videos_without_subtitles, youtube_loader, transcriber_worker, youtube_api_client):
    tasks = [
        asyncio.create_task(example_task(youtube_api_client, youtube_loader, transcriber_worker, link)) \
        for link in videos_without_subtitles
    ]
    await asyncio.gather(*tasks)
