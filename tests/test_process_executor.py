import asyncio
from time import sleep

import pytest

from process_executors.process_executor import ProcessExecutor


async def example_func(a: int, b: str) -> int:
    await asyncio.sleep(a)
    return a * 2

def sync_example(a: int, b: str) -> int:
    sleep(1)
    return a * 2

def test_init():
    executor = ProcessExecutor(example_func, a=5, b="5")
    executor.configure(q_size=333, context="fork", process_name="test_name")
    executor.set_name("test_name")

    print(executor.__repr__())

    assert executor.get_q_size() == 333


def test_launch():
    executor = ProcessExecutor(example_func, b="5")
    executor.start()

    executor.put_task(1)
    sleep(3)
    res = executor.get_result()
    assert res == 2

    if executor.is_alive():
        executor.stop()


def test_alive():
    executor = ProcessExecutor(example_func, b="5")
    executor.configure(q_size=500, context="spawn", process_name="python_test_process")
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
    executor = ProcessExecutor.get_instance(example_func, b="5")
    executor.configure(q_size=500, context="spawn", process_name="python_test_process")
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
    executor = ProcessExecutor.get_instance(sync_example, b="5")
    executor.configure(q_size=500, context="spawn", process_name="python_test_process")
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
