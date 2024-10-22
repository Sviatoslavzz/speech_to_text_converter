import asyncio
import re
from collections.abc import AsyncGenerator
from pathlib import Path

from executors.process_executor import ProcessExecutor
from objects import TranscriptionTask, YouTubeVideo, get_env, get_save_dir, DownloadTask, MB
from storage.storage_worker import storage_worker_as_target
from transcribers.transcriber_worker import transcriber_worker_as_target
from youtube_workers.youtube_api import YouTubeClient
from youtube_workers.youtube_loader import YouTubeLoader


def get_clients() -> tuple[YouTubeClient, YouTubeLoader]:
    youtube_client = YouTubeClient(get_env().get("YOUTUBE_API")) \
        if not YouTubeClient.get_instance() \
        else YouTubeClient.get_instance()

    youtube_loader = YouTubeLoader(get_save_dir()) \
        if not YouTubeLoader.get_instance() \
        else YouTubeLoader.get_instance()

    return youtube_client, youtube_loader


async def convert_links_to_videos(links: str) -> AsyncGenerator[tuple[bool, str, YouTubeVideo | None], None]:
    links = re.split(r"[ ,\n]+", links)
    youtube_client, _ = get_clients()
    for link in links:
        video = await youtube_client.get_video_by_link(link.strip())
        if not video:
            yield False, link, None
        else:
            yield True, link, video


async def get_channel_videos_worker(link: str) -> tuple[bool, int, list[YouTubeVideo] | None]:
    youtube_client, _ = get_clients()
    channel_id = await youtube_client.get_channel_id_by_link(link.strip())
    if not channel_id:
        return False, 0, None
    amount, videos = await youtube_client.get_channel_videos(channel_id)
    return True, amount, videos


async def download_video_worker(task: DownloadTask) -> DownloadTask:
    """
    Sends the task for video downloading.
    If file size exceeds tg max transfer size sends the task for uploading to storage
    :param task: DownloadTask
    :return: DownloadTask
    """
    _, client = get_clients()
    result: DownloadTask = await client.download_video(task)

    if result and result.file_size > 50 * MB:
        pass  # TODO async run dropbox

    return result


async def download_audio_worker(videos: list[YouTubeVideo], chat_id: str) -> AsyncGenerator[tuple[bool, Path], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.download_audio(video=video, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link


async def download_subtitles_worker(videos: list[YouTubeVideo],
                                    chat_id: str) -> AsyncGenerator[tuple[bool, Path | str], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.get_captions(video=video, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link


async def run_transcriber_executor(tasks: list[TranscriptionTask]) -> list[TranscriptionTask]:
    """
    Runs transcriber in a separate process,
    puts transcription tasks to process Queue,
    and asynchronously wait for results
    Returns: list of TranscriptionTask
    """
    executor = ProcessExecutor.get_instance()
    if not executor:
        executor = ProcessExecutor(transcriber_worker_as_target)
        executor.configure(q_size=300, context="spawn", process_name="python_transcriber_worker")
        executor.set_name("transcriber_worker")
        executor.start()

    async def submit_task(task_: TranscriptionTask) -> TranscriptionTask:
        executor.put_task(task_)
        while True:
            result = await asyncio.to_thread(executor.get_result)
            if result:
                if task_.id == result.id:
                    return result
                executor.put_result(result)

            await asyncio.sleep(0.1)

    async_tasks = [asyncio.create_task(submit_task(task)) for task in tasks]
    process_result = await asyncio.gather(*async_tasks)

    return list(process_result)


async def run_storage_executor(tasks: list[DownloadTask]) -> list[DownloadTask]:
    """
    Runs storage_worker in a separate process,
    puts download tasks to process Queue,
    and asynchronously wait for results
    Returns: list of DownloadTask
    """
    executor = ProcessExecutor.get_instance()
    if not executor:
        executor = ProcessExecutor(storage_worker_as_target)
        executor.configure(q_size=500, context="spawn", process_name="python_storage_worker")
        executor.set_name("storage_worker")
        executor.start()

    async def submit_task(task_: DownloadTask) -> DownloadTask:
        executor.put_task(task_)
        while True:
            result = await asyncio.to_thread(executor.get_result)
            if result:
                if task_.id == result.id:
                    return result
                executor.put_result(result)

            await asyncio.sleep(0.1)

    async_tasks = [asyncio.create_task(submit_task(task)) for task in tasks]
    process_result = await asyncio.gather(*async_tasks)

    return list(process_result)