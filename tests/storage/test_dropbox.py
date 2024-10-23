import asyncio
import time

import pytest

from storage.dropbox_storage import DropBox


@pytest.fixture(scope="module")
def dropbox_client():
    client = DropBox(storage_time=30)
    client.start()
    return client


def test_connection(dropbox_client):
    assert dropbox_client.empty()


@pytest.mark.asyncio
async def test_upload_delete_cycle(dropbox_client, saving_path, files):
    for file in files:
        link = await dropbox_client.upload(local_path=(saving_path / file))
        assert "dropbox" in link
    assert not dropbox_client.empty()

    while not dropbox_client.empty():
        time.sleep(0.5)
        await dropbox_client.timer_delete()

    if dropbox_client.is_connected():
        dropbox_client.stop()


@pytest.mark.asyncio
async def test_get_space(dropbox_client):
    if not dropbox_client.is_connected():
        dropbox_client.start()

    space = await dropbox_client.storage_space()
    assert space > 500

    if dropbox_client.is_connected():
        dropbox_client.stop()


@pytest.mark.asyncio
async def test_upload_delete_cycle_async(dropbox_client, saving_path, files):
    if not dropbox_client.is_connected():
        dropbox_client.start()

    tasks = [asyncio.create_task(dropbox_client.upload(local_path=(saving_path / file))) for file in files]
    links = await asyncio.gather(*tasks)
    assert not dropbox_client.empty()
    for link in links:
        assert "dropbox" in link

    while not dropbox_client.empty():
        time.sleep(0.5)
        await dropbox_client.timer_delete()

    if dropbox_client.is_connected():
        dropbox_client.stop()


@pytest.mark.skip(reason="Only manual testing, local file required")
@pytest.mark.asyncio
async def test_heavy_file_upload(dropbox_client, saving_path):
    if not dropbox_client.is_connected():
        dropbox_client.start()

    link = await dropbox_client.upload(local_path=(saving_path / "архитектура_IT_Sibur.mp4"))
    assert "dropbox" in link
    assert not dropbox_client.empty()

    while not dropbox_client.empty():
        time.sleep(0.5)
        await dropbox_client.timer_delete()

    if dropbox_client.is_connected():
        dropbox_client.stop()


@pytest.mark.asyncio
async def test_upload_same_file(dropbox_client, saving_path, files):
    if not dropbox_client.is_connected():
        dropbox_client.start()

    link_initial = await dropbox_client.upload(local_path=(saving_path / files[0]))
    assert "dropbox" in link_initial
    link_second = await dropbox_client.upload(local_path=(saving_path / files[0]))
    assert link_initial == link_second
    while not dropbox_client.empty():
        time.sleep(0.5)
        await dropbox_client.timer_delete()

    if dropbox_client.is_connected():
        dropbox_client.stop()


@pytest.mark.asyncio
async def test_get_files(dropbox_client, saving_path, files):
    if not dropbox_client.is_connected():
        dropbox_client.start()

    for file in files:
        link = await dropbox_client.upload(local_path=(saving_path / file))
        assert "dropbox" in link
    assert not dropbox_client.empty()

    loaded_files = await dropbox_client.list_dropbox_files()
    assert loaded_files == files

    storage_files = dropbox_client.list_storage_files()
    assert storage_files == files

    while not dropbox_client.empty():
        time.sleep(0.5)
        await dropbox_client.timer_delete()

    if dropbox_client.is_connected():
        dropbox_client.stop()


@pytest.mark.skip(reason="Only manual testing, internal limit change required")
@pytest.mark.asyncio
async def test_refresh_token(dropbox_client):
    if not dropbox_client.is_connected():
        dropbox_client.start()

    # requires manually changing token timer limit ~60 sec

    assert await dropbox_client.storage_space() > 500

    await asyncio.sleep(70)

    assert await dropbox_client.storage_space() > 500

    if dropbox_client.is_connected():
        dropbox_client.stop()
