import asyncio

from loguru import logger

from executors.process_executor import ProcessExecutor


class StorageExecutor(ProcessExecutor):
    """
    Extends ProcessExecutor to handle storage operations.
    Added to constantly send signals to storages to check timers
    """

    async def _run_async_target(self, task_queue, result_queue, stop_event):
        async def process_in_target(task_):
            result = await self._target(task_, *self._target_args, **self._target_kwargs)
            if result:
                logger.info("Put result to result_queue")
                result_queue.put(result)

        async_tasks = []
        while not stop_event.is_set():
            task = None
            if not task_queue.empty():
                task = task_queue.get()
                logger.info("Got new task from task_queue")

            async_tasks.append(asyncio.create_task(process_in_target(task)))
            async_tasks = [task for task in async_tasks if not task.done()]
            await asyncio.sleep(0.5)

        if async_tasks:
            logger.warning(f"Finishing process with running async tasks ~ {len(async_tasks)}: waiting...")
            await asyncio.gather(*async_tasks)
