import asyncio
from time import sleep

import pytest

from app.main_workers import run_transcriber_executor
from executors.process_executor import ProcessExecutor
from objects import TranscriptionTask


def sync_function(a: int, b: str) -> int:
    sleep(a)
    return a * 2


async def async_function(a: int, b: str) -> int:
    await asyncio.sleep(a)
    return a * 2


def test_init():
    executor = ProcessExecutor(async_function, a=5, b="5")
    executor.configure(q_size=333, context="fork", process_name="test_name")
    executor.set_name("test_name")
    assert executor.__repr__()
    assert executor.get_q_size() == 333


@pytest.mark.parametrize(
    "process_executor",
    [{"target": sync_function, "args": (), "kwargs": {"a": 5, "b": "5"}}],
    indirect=True
)
def test_reinit_wrong(process_executor):
    process_executor.configure(process_name="test")
    executor_2 = ProcessExecutor(async_function, a=5, b="5")  # this call does not change the attributes

    assert process_executor is executor_2
    assert "test" in executor_2.__str__()


@pytest.mark.parametrize(
    "process_executor",
    [{"target": async_function, "args": (), "kwargs": {"b": "5"}}],
    indirect=True
)
def test_launch(process_executor):
    process_executor.start()

    process_executor.put_task(1)
    sleep(4)
    res = process_executor.get_result()
    assert res == 2

    process_executor.stop()


@pytest.mark.parametrize(
    "process_executor",
    [{"target": async_function, "args": (), "kwargs": {"b": "5"}}],
    indirect=True
)
def test_alive(process_executor):
    process_executor.configure(q_size=30, context="spawn", process_name="python_test_process")
    process_executor.start()
    process_executor.put_task(5)
    assert process_executor.is_alive()
    sleep(2)
    process_executor.stop()

    assert not process_executor.is_alive()


async def task_generator(task: int):
    executor = ProcessExecutor.get_instance()
    await asyncio.to_thread(executor.put_task, task)


@pytest.mark.parametrize(
    "process_executor",
    [{"target": async_function, "args": (), "kwargs": {"b": "5"}}],
    indirect=True
)
@pytest.mark.asyncio
async def test_async_target(process_executor):
    process_executor.configure(q_size=30, context="spawn", process_name="python_test_process")
    process_executor.start()

    async_tasks = []
    results = []
    for i in range(20, 0, -1):
        results.append(i * 2)
        async_tasks.append(asyncio.create_task(task_generator(i)))

    await asyncio.gather(*async_tasks)

    assert process_executor.n_tasks_running() == 20

    while process_executor.n_tasks_running():
        if not process_executor.is_result_queue_empty():
            assert process_executor.get_result() in results

    process_executor.stop()

    assert not process_executor.is_alive()


@pytest.mark.parametrize(
    "process_executor",
    [{"target": sync_function, "args": (), "kwargs": {"b": "5"}}],
    indirect=True
)
@pytest.mark.asyncio
async def test_sync_target(process_executor):
    process_executor.configure(q_size=30, context="spawn", process_name="python_test_process")
    process_executor.start()

    async_tasks = []
    results = []
    for i in range(5, 0, -1):
        results.append(i * 2)
        async_tasks.append(asyncio.create_task(task_generator(i)))

    await asyncio.gather(*async_tasks)

    while process_executor.n_tasks_running():
        if not process_executor.is_result_queue_empty():
            assert process_executor.get_result() in results

    process_executor.stop()

    assert not process_executor.is_alive()


@pytest.mark.skip(reason="Heavy transcribing, only manual run")
@pytest.mark.asyncio
async def test_e2e_with_transcriber(saving_path, files):
    """
    Runs executor with transcription tasks (5 files)
    """
    tasks = [TranscriptionTask(origin_path=saving_path / file, id=f"123_{file}") for file in files[:5]]
    results = await run_transcriber_executor(tasks)

    assert len(results) == len(tasks)

    for result in results:
        assert result.result is True
        assert result.local_path is not None
        assert result.file_size is not None
        result.local_path.unlink(missing_ok=False)

    executor = ProcessExecutor.get_instance()
    executor.stop()
    assert not executor.is_alive()


def test_relaunching():
    executor = ProcessExecutor.get_instance()
    if not executor:
        executor = ProcessExecutor(async_function, b="test")
    else:
        executor.reinitialize(async_function, b="test")

    executor.configure(q_size=30, process_name="test_1")
    executor.start()

    executor.put_task(1)
    executor.put_task(2)

    while executor.n_tasks_running():
        if not executor.is_result_queue_empty():
            assert executor.get_result() in [2, 4]

    executor.reinitialize(sync_function, b="test")
    assert not executor.is_alive()
    executor.configure(q_size=40, process_name="test_2")
    executor.start()

    executor.put_task(1)
    executor.put_task(2)

    while executor.n_tasks_running():
        if not executor.is_result_queue_empty():
            assert executor.get_result() in [2, 4]

    executor.stop()

    assert not executor.is_alive()


@pytest.mark.parametrize(
    "process_executor",
    [{"target": async_function, "args": (), "kwargs": {"b": "test"}}],
    indirect=True
)
def test_cancel_async(process_executor):
    process_executor.start()

    sleep(1)
    for i in range(20, 1, -1):
        process_executor.put_task(i)
        if i == 10:
            sleep(5)
            process_executor.stop()

    while process_executor.n_tasks_running():
        if not process_executor.is_result_queue_empty():
            assert process_executor.get_result() in range(20, 42)

    assert not process_executor.is_alive()


@pytest.mark.parametrize(
    "process_executor",
    [{"target": sync_function, "args": (), "kwargs": {"b": "test"}}],
    indirect=True
)
def test_cancel(process_executor):
    process_executor.start()
    sleep(1)
    for i in range(10, 5, -1):
        process_executor.put_task(i)
        if i == 10:
            sleep(2)
            process_executor.stop()

    while process_executor.n_tasks_running():
        if not process_executor.is_result_queue_empty():
            assert process_executor.get_result() in range(18, 21)

    assert not process_executor.is_alive()
