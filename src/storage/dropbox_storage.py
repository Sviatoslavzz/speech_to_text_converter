import time
from pathlib import Path

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import DeleteError, UploadSessionCursor, CommitInfo
from dropbox.sharing import CreateSharedLinkWithSettingsError
from loguru import logger

token = "sl.B-dEaJl5dPiJQlOGn8bIaZSNsmXuXzsDmGGnTL8mAr0uqOfvvOjpTmnBO3Bg8seLkkp7SQyaYxfyOhzuDd1oArrrplKPmbultwhy-x3f_h1j9Dp3ghqyRSOUf6FArZx00trf4Uqi4EV3zbmR-I8ujXc"
MB = 1024 * 1024


class DropBox:
    _client: dropbox.Dropbox

    def __init__(self, token: str, storage_time: float = 1800):
        self._token = token
        self._storage: dict[str, float] = {}
        self._storage_time = storage_time

    def __enter__(self):
        self._client = dropbox.Dropbox(self._token)
        logger.info(f"Dropbox started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info(f"Dropbox closed")
        self._client.close()

    def upload(self, local_path: Path, name: str) -> str | None:
        """
        Uploads local file to DropBox
        :param local_path:
        :param name: file name to save in DB
        :return: shared link to DB file | None
        """
        db_path = f"/{name}"
        try:
            if db_path not in self._storage:
                if local_path.stat().st_size > 140 * MB:  # TODO hardcode
                    self._upload_by_chunks(local_path, db_path, 16 * MB)  # TODO not async
                else:
                    with local_path.open('rb') as f:
                        self._client.files_upload(f.read(), db_path)
                self._storage[db_path] = time.time()
                logger.info(f"File uploaded to DropBox {db_path}")
                return self._client.sharing_create_shared_link_with_settings(db_path).url
            else:
                logger.info(f"File already in DropBox {db_path}")
                shared_links = self._client.sharing_list_shared_links(db_path)
                if shared_links.links:
                    return shared_links.links[0].url

        except (FileNotFoundError, dropbox.exceptions.ApiError, CreateSharedLinkWithSettingsError) as e:
            logger.error(f"An exception occurred while uploading {db_path} to DropBox {e.__repr__()}")

    def _upload_by_chunks(self, local_path: Path, db_path: str, chunk_size: int = 16 * MB):
        with local_path.open(mode="rb") as f:
            logger.info(f"Upload session started for {db_path}")
            uss_result = self._client.files_upload_session_start(f.read(chunk_size))
            session_id = uss_result.session_id
            cursor = UploadSessionCursor(session_id=session_id, offset=f.tell())
            while 1:
                data = f.read(chunk_size)
                if not data:
                    break
                logger.debug(f"uploading new chunk of size {chunk_size}")
                self._client.files_upload_session_append_v2(data, cursor)
                cursor.offset += len(data)

            self._client.files_upload_session_finish(f.read(0), cursor, CommitInfo(path=db_path))
            logger.info(f"Upload session ended for {db_path}")

    def timer_delete(self):
        keys_to_delete = []
        for file in self._storage:
            if time.time() - self._storage[file] > self._storage_time:
                logger.info(f"Found expired file {file}")
                self.delete(file)
                keys_to_delete.append(file)
        for file in keys_to_delete:
            self._storage.pop(file, None)

    def delete(self, path_: str):
        try:
            self._client.files_delete_v2(path_)
            logger.info(f"Dropbox file successfully deleted: {path_}")
        except (DeleteError, ApiError) as e:
            logger.error(f"An exception occurred while deleting from DropBox by {path_} {e.__repr__()}")

    def empty(self) -> bool:
        return len(self._storage) == 0

    def list_files(self) -> list:
        files = []
        result = self._client.files_list_folder("")
        for entry in result.entries:
            files.append(entry.name)
        return files


def main():
    with DropBox(token=token, storage_time=60) as db:
        # files = db.list_files()
        # for file in files:
        #     db.delete(f"/{file}")
        # print(await db.upload(Path("../saved_files/test_1.mp4"), name="test_1.mp4"))
        # print(await db.upload(Path("../saved_files/test_2.mp4"), name="test_2.mp4"))
        # print(await db.upload(Path("../saved_files/test_3.mp4"), name="test_3.mp4"))
        print(db.upload(Path("../saved_files/архитектура_IT_Sibur.mp4"), name="архитектура_IT_Sibur.mp4"))

        while not db.empty():
            time.sleep(1)
            db.timer_delete()


if __name__ == "__main__":
    main()
