from collections.abc import Callable

from loguru import logger

from executors.process_executor import ProcessExecutor


class TranscriberExecutor(ProcessExecutor):
    _instance = None
    _allow_reinit = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._allow_reinit = True
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, target: Callable, *target_args, **target_kwargs):
        if self._allow_reinit:
            logger.info(f"{self.__class__.__name__} initializing...")
            super().__init__(target, *target_args, **target_kwargs)

    @classmethod
    def get_instance(cls):
        """
        Returns an instance of the ProcessExecutor class if exists, None otherwise.
        """
        return cls._instance

    def reinitialize(self, target: Callable, *args, **kwargs):
        if self.is_alive():
            self.stop()
        self._allow_reinit = True
        self.__init__(target, *args, **kwargs)
