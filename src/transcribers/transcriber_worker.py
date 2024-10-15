import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any

from loguru import logger

from objects import TranscriptionTask
from transcribers.abscract import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber


class TranscriberWorker:
    _instance = None
    _WHISPER_MODEL = "small"
    _TRANSCRIBER: type[AbstractTranscriber] = FasterWhisperTranscriber

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        self.transcriber = self._TRANSCRIBER(model=self._WHISPER_MODEL)
        self.semaphore = asyncio.Semaphore(4)  # TODO config
        self.pool = ThreadPoolExecutor(max_workers=4)
        logger.info("TranscriberWorker initialized")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    @staticmethod
    def _async_wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):  # noqa ANN202
            async with self.semaphore:
                loop = asyncio.get_running_loop()
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
            result = self.transcriber.transcribe(path=task.origin_path)
        except NotImplementedError as e:
            task.result = False
            task.message.available_languages.append("en")
            task.message.message = {"ru": "Неверное расширение файла",
                                    "en": "File format is not supported"}
            return task

        task.transcription_path = task.origin_path.with_suffix(".txt")

        try:
            with task.transcription_path.open(mode="w") as file:
                file.write(result)
            logger.info(f"Transcription saved\nwhere: {task.transcription_path}")
            task.result = True
        except OSError:
            logger.error(f"Unable to save transcription to {task.transcription_path}")
            task.result = False
            task.message.message = {"ru": "Не получилось сохранить транскрипцию"}

        return task
