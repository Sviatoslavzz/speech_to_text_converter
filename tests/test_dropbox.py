import time

from storage.dropbox_storage import DropBox


def test_connection():
    with DropBox(storage_time=60) as dp_client:
        assert dp_client.empty()


def test_upload_delete_cycle(saving_path, files):
    with DropBox(storage_time=30) as dp_client:
        for file in files:
            link = dp_client.upload(local_path=(saving_path / file))
            assert "dropbox" in link
        assert not dp_client.empty()

        while not dp_client.empty():
            time.sleep(0.5)
            dp_client.timer_delete()


def test_get_space():
    with DropBox(storage_time=30) as dp_client:
        space = dp_client.storage_space()
        assert space > 500
