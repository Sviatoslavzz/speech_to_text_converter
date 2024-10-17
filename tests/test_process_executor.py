import asyncio
from time import sleep

import pytest

from app.main_workers import run_transcriber_executor
from objects import TranscriptionTask
from process_executors.process_executor import ProcessExecutor


def sync_example(a: int, b: str) -> int:
    sleep(1)
    return a * 2


async def async_example(a: int, b: str) -> int:
    await asyncio.sleep(a)
    return a * 2


def test_init():
    executor = ProcessExecutor(async_example, a=5, b="5")
    executor.configure(q_size=333, context="fork", process_name="test_name")
    executor.set_name("test_name")
    assert executor.__repr__()
    assert executor.get_q_size() == 333


def test_launch():
    executor = ProcessExecutor(async_example, b="5")
    executor.start()

    executor.put_task(1)
    sleep(4)
    res = executor.get_result()
    assert res == 2

    executor.stop()


def test_alive():
    executor = ProcessExecutor(async_example, b="5")
    executor.configure(q_size=30, context="spawn", process_name="python_test_process")
    executor.start()
    executor.put_task(5)
    assert executor.is_alive()
    sleep(2)
    executor.stop()

    assert not executor.is_alive()


async def task_generator(task: int):
    executor = ProcessExecutor.get_instance()
    await asyncio.to_thread(executor.put_task, task)


@pytest.mark.asyncio
async def test_parallel_tasks():
    executor = ProcessExecutor.get_instance(async_example, b="5")
    executor.configure(q_size=30, context="spawn", process_name="python_test_process")
    executor.start()

    async_tasks = []
    results = []
    for i in range(20, 0, -1):
        results.append(i * 2)
        async_tasks.append(asyncio.create_task(task_generator(i)))

    await asyncio.gather(*async_tasks)

    assert executor.n_tasks_running() == 20

    while executor.n_tasks_running():
        if not executor.is_result_queue_empty():
            assert executor.get_result() in results

    executor.stop()

    assert not executor.is_alive()


@pytest.mark.asyncio
async def test_sync_target():
    executor = ProcessExecutor(sync_example, b="5")
    executor.configure(q_size=30, context="spawn", process_name="python_test_process")
    executor.start()

    async_tasks = []
    results = []
    for i in range(20, 0, -1):
        results.append(i * 2)
        async_tasks.append(asyncio.create_task(task_generator(i)))

    await asyncio.gather(*async_tasks)

    while executor.n_tasks_running():
        if not executor.is_result_queue_empty():
            assert executor.get_result() in results

    executor.stop()

    assert not executor.is_alive()


@pytest.mark.asyncio
async def test_e2e_with_transcriber(saving_path, files):
    """
    WARNING: this test uses SINGLETON process executor class, which is not reset bw tests
    """
    tasks = [TranscriptionTask(origin_path=saving_path / file, id=f"123_{file}") for file in files]
    results = await run_transcriber_executor(tasks)

    assert len(results) == len(tasks)

    for result in results:
        assert result.result is True
        assert result.transcription_path is not None
        assert result.file_size is not None
        result.transcription_path.unlink(missing_ok=False)

    executor = ProcessExecutor.get_instance()
    executor.stop()
    assert not executor.is_alive()
