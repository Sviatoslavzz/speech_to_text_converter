import asyncio
from time import sleep

from numba.cuda.cudadrv.nvvm import logger

from process_executors.process_executor import ProcessExecutor


async def example_func(a: int, b: str) -> int:
    print(b)
    await asyncio.sleep(0.5)
    return a * 2


def test_init():
    executor = ProcessExecutor(example_func, process_name="new_process", a=5, b="5")
    executor.configure(q_size=333, context="fork")
    executor.set_name("test_name")

    print(executor.__repr__())

    assert executor.get_q_size() == 333


def test_launch():
    executor = ProcessExecutor(example_func, process_name="new_process", b="5")
    executor.start()

    executor.put_task(5)
    sleep(2)
    res = executor.get_result()
    assert res == 10

    if executor.is_alive():
        executor.kill()


def test_alive():
    executor = ProcessExecutor(example_func, process_name="new_process", b="5")
    executor.start()
    executor.put_task(5)
    assert executor.is_alive()

    executor.kill()

    assert not executor.is_alive()
