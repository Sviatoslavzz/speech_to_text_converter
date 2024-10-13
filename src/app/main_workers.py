import asyncio
import time
from multiprocessing import get_context, Queue
import re
from collections.abc import AsyncGenerator
from pathlib import Path

from objects import get_env, get_save_dir

from objects import YouTubeVideo
from transcribers.worker import TranscriberWorker
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
    while True:
        if not task_queue.empty():
            task = task_queue.get()
            logger.debug(f"PROCESS GOT TASK {task}")
            result, path_ = await tr_worker.transcribe(task[1])
            result_queue.put((task[0], result, path_))

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


async def run_transcriber_executor(local_files: list[Path], uid: int, mess_id: int) -> list[(bool, Path)]:
    """
    Runs a transcriber executor in a separate process
    Passes local files for transcribing
    :return: list of path to text files
    """
    if not TRANSCRIBER_WORKER.is_alive():
        time.sleep(2)
        TRANSCRIBER_WORKER.start()
        logger.debug(f"TRANSCRIBER_WORKER started")

    tasks = []
    # need to form task ID to properly take it from Queue
    for i in range(len(local_files)):
        tasks.append(asyncio.create_task(submit_transcriber_task((f"{uid}{mess_id}{i}", local_files[i]))))
    process_result = await asyncio.gather(*tasks)

    return [result for result in process_result]


async def submit_transcriber_task(task):
    TRANSCRIBE_TASK_QUEUE.put(task)
    logger.debug(f"TASK PUT {task}")
    while True:
        if not TRANSCRIBE_RESULT_QUEUE.empty():
            result_id, result, path_ = await asyncio.to_thread(TRANSCRIBE_RESULT_QUEUE.get,)
            logger.debug(f"TASK GET {result_id}")
            if task[0] == result_id:
                return result, path_
            else:
                TRANSCRIBE_RESULT_QUEUE.put((result_id, result, path_))

        await asyncio.sleep(0.1)
