import asyncio
from collections.abc import Callable
from multiprocessing import Event, Queue, get_context
from typing import Any

from loguru import logger
from setproctitle import setproctitle

from executors.abstract_executor import AbstractExecutor


class ProcessExecutor(AbstractExecutor):
    """
    A process executor.
    Creates a separate process with a <target> function and runs it.
    Accepts tasks and passes them to tasks queue for <target>
    Results are put to result queue.
    """

    _context = "spawn"

    def __init__(self, target: Callable, *target_args, **target_kwargs):
        self._process_name = None
        self._worker = None
        self._tasks_running = 0
        super().__init__(target, *target_args, **target_kwargs)
        self._allow_reinit = False

    def configure(self, q_size: int = 500, context: str = "spawn", process_name: str | None = None):
        self._q_size = q_size
        self._context = context
        self._process_name = process_name

    def is_task_queue_empty(self) -> bool:
        return not self._task_queue or self._task_queue.empty()

    def is_result_queue_empty(self) -> bool:
        return not self._result_queue or self._result_queue.empty()

    def put_task(self, task: Any):
        if not self._stop_event.is_set():
            self._tasks_running += 1
            logger.info(f"{self.__class__.__name__} {self._name} has {self._tasks_running} tasks in operation")
            self._task_queue.put(task)

    def put_result(self, task: Any):
        self._tasks_running += 1
        self._result_queue.put(task)

    def get_result(self) -> Any:
        if not self._result_queue.empty():
            self._tasks_running -= 1
            logger.info(f"{self.__class__.__name__} {self._name} has {self._tasks_running} tasks in operation")
            return self._result_queue.get()
        return None

    def is_alive(self):
        return bool(self._worker) and self._worker.is_alive()

    def start(self):
        """
        If process is not running:
        Creates queues and runs the worker with a <target> func
        """
        if not self.is_alive():
            self._task_queue = Queue(maxsize=self._q_size)
            self._result_queue = Queue(maxsize=self._q_size)
            self._stop_event = Event()
            self._worker = get_context(self._context).Process(
                target=self._run_target,
                name=self._process_name,
                args=(self._task_queue, self._result_queue, self._stop_event),
            )

            self._worker.start()
            logger.info(
                f"{self.__class__.__name__} {self._name} q_size={self._q_size}, context={self._context} started"
            )
            return
        logger.warning(f"{self.__class__.__name__} {self._name} already running")

    def _run_target(self, task_queue, result_queue, stop_event):
        if self._process_name:
            setproctitle(self._process_name)
        if asyncio.iscoroutinefunction(self._target):
            logger.info(f"Found coroutine target {self._target.__name__}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_async_target(task_queue, result_queue, stop_event))
        else:
            logger.info(f"Found target {self._target.__name__}")
            self._run_sync_target(task_queue, result_queue, stop_event)

    def stop(self):
        self._stop_event.set()
        if self.is_alive():
            self._worker.join()
        logger.info(f"{self.__class__.__name__} {self._name} stopped")

    def n_tasks_running(self) -> int:
        return self._tasks_running

    def __str__(self):
        cls_ = f"class: {self.__class__.__name__}"
        name_ = f"name: {self._name}"
        proc_name = f"process_name: {self._process_name}"
        qs = f"q_size: {self._q_size}"
        cxt = f"context: {self._context}"
        return f"{cls_}, {name_}, {proc_name}, {qs}, {cxt}"

    def __repr__(self):
        return f"{self.__class__.__name__} (q_size: {self._q_size}, context: {self._context})"
