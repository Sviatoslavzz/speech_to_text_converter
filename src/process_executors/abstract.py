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
    _name: str | None = "default name"

    def __init__(self, target: Callable, *target_args, **target_kwargs):  # TODO config
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_async_target(task_queue, result_queue))
        else:
            self._run_sync_target(task_queue, result_queue)

    def _run_sync_target(self, task_queue, result_queue):
        logger.debug("ENTERING LOOP")
        while True:
            if not task_queue.empty():
                task = task_queue.get()
                logger.debug(f"PROCESS GOT TASK {task}")
                result = self._target(task, *self._target_args, **self._target_kwargs)
                result_queue.put(result)

    async def _run_async_target(self, task_queue, result_queue):
        logger.debug("ENTERING LOOP")

        async def process_in_target(task_):
            result = await self._target(task_, *self._target_args, **self._target_kwargs)
            result_queue.put(result)

        while True:
            if not task_queue.empty():
                task = task_queue.get()
                logger.debug(f"PROCESS GOT TASK {task}")
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
