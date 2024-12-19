import time
from asyncio import get_running_loop
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any

from loguru import logger

from config.conf_models import TranscriberConfig
from objects import TranscriptionTask


class TranscriberWorker:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, config: TranscriberConfig):
        self.transcriber = config.cls(model=config.model)
        self.pool = ThreadPoolExecutor(max_workers=config.pool_size)

        logger.info(f"{self.__class__.__name__} initialized")

    @classmethod
    def get_instance(cls):
        return cls._instance

    @staticmethod
    def _async_wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):  # ANN202
            loop = get_running_loop()
            return await loop.run_in_executor(self.pool, lambda: func(self, *args, **kwargs))

        return wrapper

    @staticmethod
    def file_exist(task: TranscriptionTask) -> bool:
        if not task.origin_path.is_file():
            logger.error(f"{task.id} File does not exist: {task.origin_path}")
            task.result = False
            task.message.message = {"ru": "Не нашел файл для транскрибации"}
            return False

        return True

    @_async_wrap
    def transcribe(self, task: TranscriptionTask) -> TranscriptionTask:
        """
        Checks the origin_path, launches transcription process, saves the result in .txt
        :param task: TranscriptionTask with filled origin path
        :return: TranscriptionTask
        """

        if not self.file_exist(task):
            return task

        try:
            transcription = self.transcriber.transcribe(path=task.origin_path)
        except NotImplementedError:
            task.result = False
            task.message.available_languages.append("en")
            task.message.message = {"ru": "Неверное расширение файла",
                                    "en": "File format is not supported"}
            return task

        task.local_path = task.origin_path.with_suffix(".txt")

        try:
            with task.local_path.open(mode="w") as file:
                file.write(transcription)
            logger.info(f"Transcription saved\nwhere: {task.local_path}")
            task.result = True
            task.file_size = task.local_path.stat().st_size
        except OSError:
            logger.error(f"Unable to save transcription to {task.local_path}")
            task.result = False
            task.message.message = {"ru": "Не получилось сохранить транскрипцию"}

        return task


async def transcriber_worker_as_target(task: TranscriptionTask, config: TranscriberConfig) -> TranscriptionTask:
    worker = TranscriberWorker.get_instance()
    if not worker:
        worker = TranscriberWorker(config=config)
        time.sleep(1)  # blocking pause to wait for TranscriberWorker init

    return await worker.transcribe(task)
