import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Any

from loguru import logger

from transcribers.abscract import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber

# from transcribers.whisper_transcriber import WhisperTranscriber


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
        self.semaphore = asyncio.Semaphore(4)
        self.pool = ThreadPoolExecutor(max_workers=4)
        logger.info("TranscriberWorker initialized")

    @classmethod
    def get_instance(cls):
        return cls._instance

    @staticmethod
    def _async_wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):  # noqa ANN202
            async with self.semaphore:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(self.pool, lambda: func(self, *args, **kwargs))

        return wrapper

    @_async_wrap
    def transcribe(self, file_path: Path) -> tuple[bool, Path]:
        """
        Checks the save_dir, launches transcription process, saves the result in .txt
        :param transcriber: current class
        :param file_path: source file path
        :return: True in case of successful transcription, False otherwise
        """
        if not file_path.is_file():
            logger.error(f"File does not exist: {file_path}")
            raise FileNotFoundError(f"{file_path} not found")

        result = self.transcriber.transcribe(path=file_path)
        target_file = file_path.with_suffix(".txt")

        try:
            with target_file.open(mode="w") as file:
                file.write(result)
            logger.info(f"Transcription saved\nwhere: {target_file}")
            return True, file_path.with_suffix(".txt")
        except OSError as err:
            logger.error(f"Unable to save transcription to {target_file}")