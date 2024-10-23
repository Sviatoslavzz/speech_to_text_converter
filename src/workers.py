import asyncio
import re
from collections.abc import AsyncGenerator

from executors.process_executor import ProcessExecutor
from executors.storage_executor import StorageExecutor
from objects import TranscriptionTask, YouTubeVideo, get_env, get_save_dir, DownloadTask, MB
from storage.storage_worker import storage_worker_as_target
from transcribers.transcriber_worker import transcriber_worker_as_target
from youtube_clients.youtube_api import YouTubeClient
from youtube_clients.youtube_loader import YouTubeLoader


def get_api_client() -> YouTubeClient:
    return YouTubeClient(
        get_env().get("YOUTUBE_API")) if not YouTubeClient.get_instance() else YouTubeClient.get_instance()


def get_loader() -> YouTubeLoader:
    return YouTubeLoader(get_save_dir()) if not YouTubeLoader.get_instance() else YouTubeLoader.get_instance()


async def convert_links_to_videos(links: str) -> AsyncGenerator[tuple[bool, str, YouTubeVideo | None], None]:
    links = re.split(r"[ ,\n]+", links)
    for link in links:
        video = await get_api_client().get_video_by_link(link.strip())
        if not video:
            yield False, link, None
        else:
            yield True, link, video


async def get_channel_videos(link: str) -> tuple[bool, int, list[YouTubeVideo] | None]:
    channel_id = await get_api_client().get_channel_id_by_link(link.strip())
    if not channel_id:
        return False, 0, None
    amount, videos = await get_api_client().get_channel_videos(channel_id)
    return True, amount, videos


async def check_file_size(task: DownloadTask | TranscriptionTask) -> DownloadTask | TranscriptionTask:
    if task.result and task.file_size > 50 * MB:
        tasks = await run_storage_executor([task])
        return tasks[0]
    return task


async def download_video_worker(task: DownloadTask) -> DownloadTask:
    """
    Sends the task for video downloading.
    If file size exceeds tg max transfer size sends the task for uploading to storage
    :param task: DownloadTask
    :return: filled DownloadTask
    """
    task: DownloadTask = await get_loader().download_video(task)

    return await check_file_size(task)


async def download_audio_worker(task: DownloadTask) -> DownloadTask:
    """
    Sends the task for audio downloading.
    If file size exceeds tg max transfer size sends the task for uploading to storage
    :param task: DownloadTask
    :return: filled DownloadTask
    """
    task: DownloadTask = await get_loader().download_audio(task)

    return await check_file_size(task)


async def download_subtitles_worker(task: DownloadTask) -> DownloadTask:
    """
    Sends the task for subtitles downloading.
    If file size exceeds tg max transfer size sends the task for uploading to storage
    :param task: DownloadTask
    :return: filled DownloadTask
    """
    task: DownloadTask = await get_loader().get_captions(task)

    return await check_file_size(task)


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
    executor = StorageExecutor.get_instance()
    if not executor:
        executor = StorageExecutor(storage_worker_as_target)
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
