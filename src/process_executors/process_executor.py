from process_executors.abstract import AbstractExecutor
from typing import Callable, Any
from multiprocessing import get_context, Queue
import asyncio
from loguru import logger


class ProcessExecutor(AbstractExecutor):
    _instance = None
    _context = "spawn"

    def __init__(self, target: Callable, *target_args, process_name: str | None = None, **target_kwargs):
        super().__init__(target, *target_args, **target_kwargs)
        self._process_name = process_name
        self._task_queue = None
        self._result_queue = None
        self._worker = None
        logger.info(f"ProcessExecutor {self._process_name or ""} initialized")

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    def configure(self, q_size: int, context: str = "spawn"):
        self._q_size = q_size
        self._context = context

    def _run_executor(self, task_queue, result_queue):
        asyncio.run(self._run(task_queue, result_queue))

    async def _run(self, task_queue, result_queue):
        logger.debug(f"ENTERING LOOP")

        async def process_in_target(task_):
            result = await self._target(task_, *self._target_args, **self._target_kwargs)
            result_queue.put(result)

        while True:
            if not task_queue.empty():
                task = task_queue.get()
                logger.debug(f"PROCESS GOT TASK {task}")
                asyncio.create_task(process_in_target(task))
            await asyncio.sleep(0.2)

    def put_task(self, task: Any) -> Any:
        self._task_queue.put(task)
        logger.debug(f"TASK PUT {task}")

    def put_result(self, task: Any) -> Any:
        self._result_queue.put(task)
        logger.debug(f"TASK PUT BACK {task}")

    def get_result(self) -> Any:
        if not self._result_queue.empty():
            logger.debug(f"GETTING TASK FROM QUEUE")
            return self._result_queue.get()

    def kill(self):
        if self.is_alive():
            self._worker.terminate()

    def is_alive(self):
        return self._worker and self._worker.is_alive()

    def start(self):
        if not self.is_alive():
            self._task_queue = Queue(maxsize=self._q_size)
            self._result_queue = Queue(maxsize=self._q_size)
            self._worker = get_context(self._context).Process(target=self._run_executor,
                                                              name=self._process_name,
                                                              args=(self._task_queue, self._result_queue))
            self._worker.start()
            logger.info(f"Process executor {self._name} (q_size: {self._q_size}, context: {self._context}) started")

    # def __enter__(self):
    #     self._task_queue = Queue(maxsize=self._q_size)
    #     self._result_queue = Queue(maxsize=self._q_size)
    #     self._worker = get_context(self._context).Process(target=self._run_executor,
    #                                                       name=self._process_name,
    #                                                       args=(self._task_queue, self._result_queue))
    #     self._worker.start()
    #     logger.info(f"Process executor {self._name} (q_size: {self._q_size}, context: {self._context}) started")
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     if self._worker.is_alive():
    #         self._worker.terminate()
    #     return True

    def __repr__(self):
        return f"Process executor {self._name} (q_size: {self._q_size}, context: {self._context})"
