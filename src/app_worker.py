import asyncio
import platform
import re
from collections.abc import AsyncGenerator, Callable
from pathlib import Path

import aiofiles.os
from loguru import logger

from config.models import BaseConfig
from executors.process_executor import ProcessExecutor
from executors.storage_executor import StorageExecutor
from grpc_service.client import GrpcClient
from objects import MB, DownloadTask, VideoOptions, YouTubeVideo
from storage.storage_worker import storage_worker_as_target
from utils import convert_to_m4a
from youtube_clients.youtube_api import YouTubeClient
from youtube_clients.youtube_loader import YouTubeLoader

IS_MACOS = platform.system() == "Darwin"


class AppWorker:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, service_config: BaseConfig):
        self.config = service_config
        self.youtube_client = YouTubeClient(self.config.youtube.api_key_env)
        self.loader = YouTubeLoader(directory=self.config.youtube.save_dir,
                                    heavy_pool_size=self.config.youtube.heavy_pool_size,
                                    light_pool_size=self.config.youtube.light_pool_size,
                                    proxy=self.config.youtube.proxies or None)

        # semaphore is limiting the number of threads that awaits separate process queue results
        self.semaphore = asyncio.Semaphore(self.config.youtube.light_pool_size * 2)
        self.sem_queue_size = 0
        self.grpc_client = GrpcClient(self.config.grpc)

        logger.debug("{cls} initialized", cls=self.__class__.__name__)

    @classmethod
    def get_instance(cls):
        return cls._instance

    @staticmethod
    async def remove_file(file: Path) -> None:
        try:
            await aiofiles.os.unlink(file)
        except FileNotFoundError:
            logger.error("File not found : unable to remove {f_name}", f_name=file.__fspath__())

    @staticmethod
    async def launch_one_coroutine(async_worker: Callable, id_: str, videos: list[YouTubeVideo],
                                   options: VideoOptions) -> AsyncGenerator[list[asyncio.Task], None]:
        for video in videos:
            yield [asyncio.create_task(async_worker(DownloadTask(video=video, id=id_, options=options)))]

    @staticmethod
    def launch_coroutines(async_worker: Callable, id_: str, videos: list, options: VideoOptions) -> list[asyncio.Task]:
        return [
            asyncio.create_task(
                async_worker(
                    DownloadTask(
                        video=video,
                        id=id_,
                        options=options,
                    )
                )
            )
            for video in videos
        ]

    async def get_video_options(self, video: YouTubeVideo):
        return await self.loader.get_video_options(video.link)

    async def convert_links_to_videos(self, links: str) -> AsyncGenerator[tuple[bool, str, YouTubeVideo | None], None]:
        links = re.split(r"[ ,\n]+", links)
        unique_ids = []
        for link in links:
            video_id = self.youtube_client.get_video_id(link.strip(" ,.'\"-"))
            if video_id and video_id not in unique_ids:
                unique_ids.append(video_id)
                video = await self.youtube_client.get_video_by_id(video_id)
                if video:
                    yield True, link, video
                else:
                    yield False, link, None

    async def get_channel_videos(self, link: str) -> tuple[bool, int, list[YouTubeVideo] | None]:
        channel_id = await self.youtube_client.get_channel_id_by_link(link.strip())
        if not channel_id:
            return False, 0, None
        amount, videos = await self.youtube_client.get_channel_videos(channel_id)
        return True, amount, videos

    async def check_file_size(self, task: DownloadTask) -> DownloadTask:
        """
        If files size exceeds limit sends Task to StorageExecutor.
        :param task: DownloadTask
        :return: DownloadTask
        """
        if task.result and self.config.bot.server == "telegram" and task.file_size > 50 * MB:
            if not self.config.storage.storages:
                task.result = False
                task.message.message = {"ru": "К сожалению, невозможно передать файл больше 50 мб."}
                await self.remove_file(task.local_path)
                logger.error("Failed attempt to transfer file > 50 MB directly to TG without storage.\n"
                             "Please set up at least 1 storage or use local server.")
                return task

            if task.id in task.local_path.__fspath__():
                task.local_path = task.local_path.rename(
                    task.local_path.with_name(task.local_path.name.lstrip(task.id)))
            tasks = await self.run_storage_executor([task])
            return tasks[0]

        return task

    async def download_video_worker(self, task: DownloadTask) -> DownloadTask:
        """
        Sends the task for video downloading.
        If file size exceeds tg max transfer size sends the task for uploading to storage
        :param task: DownloadTask
        :return: filled DownloadTask
        """
        task: DownloadTask = await self.loader.download_video(task)

        return await self.check_file_size(task)

    async def download_audio_worker(self, task: DownloadTask) -> DownloadTask:
        """
        Sends the task for audio downloading.
        If file size exceeds tg max transfer size sends the task for uploading to storage
        :param task: DownloadTask
        :return: filled DownloadTask
        """
        task: DownloadTask = await self.loader.download_audio(task)

        return await self.check_file_size(task)

    async def download_subtitles_worker(self, task: DownloadTask) -> DownloadTask:
        """
        Sends the task for captions downloading.
        If file size exceeds tg max transfer size sends the task for uploading to storage
        :param task: DownloadTask
        :return: filled DownloadTask
        """
        task: DownloadTask = await self.loader.get_captions(task)

        return await self.check_file_size(task)

    async def request_transcription_api(self, message, file) -> tuple[bool, Path | None]:
        """
        Downloads file from tg to local.
        Converts file to .m4a.
        Streams a file to 'talkushka_whisper' service via gRPC.
        :param message: aiogram Message
        :param file: aiogram File
        :return: (bool status, Path to text file)
        """

        if not await self.grpc_client.connected:
            return False, None

        # waits for complete load in case of 'local' tg server
        file_info = await message.bot.get_file(file.file_id)

        if self.config.bot.server == "telegram":
            local_path = self.config.youtube.save_dir / f"{message.message_id!s}_{file.file_name}"
            await message.bot.download_file(file_info.file_path, destination=local_path)
        else:
            local_path = Path(file_info.file_path)

        self.sem_queue_size += 1
        async with self.semaphore:
            self.sem_queue_size -= 1
            logger.info("{cls} : tasks waiting in semaphore {size}",
                        cls=self.__class__.__name__,
                        size=self.sem_queue_size)
            status, audio_file_path = await asyncio.to_thread(convert_to_m4a, local_path)

        await self.remove_file(local_path)

        if not status:
            return False, None

        return await self.grpc_client.stream_audio_file(audio_file_path)

    async def submit_task(self, executor: ProcessExecutor, task_: DownloadTask) -> DownloadTask:
        """
        Transfer a task to executor and waits for the result in a separate thread
        :param executor: ProcessExecutor
        :param task_: DownloadTask
        """
        self.sem_queue_size += 1
        async with self.semaphore:
            self.sem_queue_size -= 1
            logger.info("{cls} : tasks waiting in semaphore {size}",
                        cls=self.__class__.__name__,
                        size=self.sem_queue_size)
            executor.put_task(task_)
            while True:
                result = await asyncio.to_thread(executor.get_result)
                if result:
                    if task_.id == result.id:
                        return result
                    executor.put_result(result)

                await asyncio.sleep(0.1)

    async def run_storage_executor(self, tasks: list[DownloadTask]) -> list[DownloadTask]:
        """
        Runs storage_worker in a separate process,
        puts download tasks to process Queue,
        and asynchronously wait for results
        Returns: list of DownloadTask
        """
        executor = StorageExecutor.get_instance()
        if not executor:
            executor = StorageExecutor(storage_worker_as_target, config=self.config.storage.storages)
            executor.configure(q_size=self.config.storage.q_size,
                               context="spawn" if IS_MACOS else "fork",
                               process_name="python_storage_worker")
            executor.set_name("storage_worker")
            executor.start()
            await asyncio.sleep(5)  # delay for storage worker to start all storages

        async_tasks = [asyncio.create_task(self.submit_task(executor, task)) for task in tasks]
        process_result = await asyncio.gather(*async_tasks)

        return list(process_result)
