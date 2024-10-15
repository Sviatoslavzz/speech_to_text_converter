import asyncio
from multiprocessing import get_context, Queue
import re
from collections.abc import AsyncGenerator
from pathlib import Path

from objects import get_env, get_save_dir, TranscriptionTask

from objects import YouTubeVideo
from transcribers.transcriber_worker import TranscriberWorker
from youtube_workers.youtube_api import YouTubeClient
from youtube_workers.yt_dlp_loader import YouTubeLoader
from loguru import logger

SAVING_FOLDER = "saved_files"
CTX = get_context("spawn")
TRANSCRIBE_TASK_QUEUE: Queue = CTX.Queue(maxsize=500)
TRANSCRIBE_RESULT_QUEUE: Queue = CTX.Queue(maxsize=500)


def run_executor(task_queue: Queue, result_queue: Queue):
    asyncio.run(async_executor(task_queue, result_queue))


async def async_executor(task_queue: Queue, result_queue: Queue):
    tr_worker = TranscriberWorker().get_instance()
    logger.debug(f"ENTERING LOOP")

    async def process_transcribe(task_):
        result = await tr_worker.transcribe(task_)
        result_queue.put(result)

    while True:
        if not task_queue.empty():
            task = task_queue.get()
            logger.debug(f"PROCESS GOT TASK {task.id}")
            asyncio.create_task(process_transcribe(task))

        await asyncio.sleep(0.1)


TRANSCRIBER_WORKER = CTX.Process(target=run_executor,
                                 args=(TRANSCRIBE_TASK_QUEUE, TRANSCRIBE_RESULT_QUEUE),
                                 name="python_transcriber")


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


async def download_video_worker(videos: list[YouTubeVideo], chat_id: str) -> AsyncGenerator[tuple[bool, Path], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.download_video(video=video, required_height=480, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link


async def download_audio_worker(videos: list[YouTubeVideo], chat_id: str) -> AsyncGenerator[tuple[bool, Path], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.download_audio(video=video, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link


async def download_subtitles_worker(videos: list[YouTubeVideo], chat_id: str) -> AsyncGenerator[
    tuple[bool, Path | str], None]:
    _, youtube_loader = get_clients()
    for video in videos:
        result, path_ = await youtube_loader.get_captions(video=video, uid=chat_id)
        if result:
            yield result, path_
        else:
            yield False, video.link


async def run_transcriber_executor(tasks: list[TranscriptionTask]) -> list[TranscriptionTask]:
    if not TRANSCRIBER_WORKER.is_alive():
        await asyncio.sleep(2)
        TRANSCRIBER_WORKER.start()
        logger.debug(f"TRANSCRIBER_WORKER process started")

    async_tasks = []
    for task in tasks:
        async_tasks.append(asyncio.create_task(submit_transcriber_task(task)))
    process_result = await asyncio.gather(*async_tasks)

    return [result for result in process_result]


async def submit_transcriber_task(task: TranscriptionTask) -> TranscriptionTask:
    TRANSCRIBE_TASK_QUEUE.put(task)
    logger.debug(f"TASK PUT {task.id}")
    while True:
        if not TRANSCRIBE_RESULT_QUEUE.empty():
            result = await asyncio.to_thread(TRANSCRIBE_RESULT_QUEUE.get, )
            logger.debug(f"TASK GET {result.id}")
            if task.id == result.id:
                return result
            else:
                TRANSCRIBE_RESULT_QUEUE.put(result)

        await asyncio.sleep(0.1)
