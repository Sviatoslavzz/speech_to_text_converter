import asyncio
import time

import pytest

from storage.dropbox_storage import DropBox


def test_connection():
    with DropBox(storage_time=60) as dp_client:
        assert dp_client.empty()


@pytest.mark.asyncio
async def test_upload_delete_cycle(saving_path, files):
    with DropBox(storage_time=30) as dp_client:
        for file in files:
            link = await dp_client.upload(local_path=(saving_path / file))
            assert "dropbox" in link
        assert not dp_client.empty()

        while not dp_client.empty():
            time.sleep(0.5)
            await dp_client.timer_delete()


@pytest.mark.asyncio
async def test_get_space():
    with DropBox(storage_time=30) as dp_client:
        space = await dp_client.storage_space()
        assert space > 500


@pytest.mark.asyncio
async def test_upload_delete_cycle_async(saving_path, files):
    with DropBox(storage_time=30) as dp_client:
        tasks = [asyncio.create_task(dp_client.upload(local_path=(saving_path / file))) for file in files]
        links = await asyncio.gather(*tasks)
        assert not dp_client.empty()
        for link in links:
            assert "dropbox" in link

        while not dp_client.empty():
            time.sleep(0.5)
            await dp_client.timer_delete()

@pytest.mark.skip(reason="Only manual testing, local file required")
@pytest.mark.asyncio
async def test_heavy_file_upload(saving_path):
    with DropBox(storage_time=60) as dp_client:
        link = await dp_client.upload(local_path=(saving_path / "архитектура_IT_Sibur.mp4"))
        assert "dropbox" in link
        assert not dp_client.empty()

        while not dp_client.empty():
            time.sleep(0.5)
            await dp_client.timer_delete()

@pytest.mark.asyncio
async def test_upload_same_file(saving_path, files):
    with DropBox(storage_time=30) as dp_client:
        link_initial = await dp_client.upload(local_path=(saving_path / files[0]))
        assert "dropbox" in link_initial
        link_second = await dp_client.upload(local_path=(saving_path / files[0]))
        assert link_initial == link_second
        while not dp_client.empty():
            time.sleep(0.5)
            await dp_client.timer_delete()

