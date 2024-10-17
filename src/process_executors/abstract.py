import asyncio
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from loguru import logger


class AbstractExecutor:
    _q_size: int = 500
    _target: Callable
    _target_args: tuple[Any, ...]
    _target_kwargs: dict[Any, Any]
    _name: str | None = "-"

    def __init__(self, target: Callable, *target_args, **target_kwargs):
        self._target = target
        self._target_args = target_args
        self._target_kwargs = target_kwargs

    def configure(self, q_size: int):
        self._q_size = q_size

    def set_name(self, name: str):
        self._name = name

    def get_q_size(self) -> int:
        return self._q_size

    def _run_target(self, task_queue, result_queue):
        if asyncio.iscoroutinefunction(self._target):
            logger.info(f"Found coroutine target {self._target.__name__}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_async_target(task_queue, result_queue))
        else:
            logger.info(f"Found target {self._target.__name__}")
            self._run_sync_target(task_queue, result_queue)

    def _run_sync_target(self, task_queue, result_queue):
        while True:
            if not task_queue.empty():
                task = task_queue.get()
                logger.info(f"Got new task from task_queue")
                result = self._target(task, *self._target_args, **self._target_kwargs)
                logger.info(f"Put result to result_queue")
                result_queue.put(result)

    async def _run_async_target(self, task_queue, result_queue):
        async def process_in_target(task_):
            result = await self._target(task_, *self._target_args, **self._target_kwargs)
            logger.info(f"Put result to result_queue")
            result_queue.put(result)

        while True:
            if not task_queue.empty():
                task = task_queue.get()
                logger.info(f"Got new task from task_queue")
                asyncio.create_task(process_in_target(task))

            await asyncio.sleep(0.05)

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def __repr__(self):
        pass
