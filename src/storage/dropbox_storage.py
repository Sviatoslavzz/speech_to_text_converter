import time
from pathlib import Path
import asyncio

import dropbox
import requests
from dropbox.exceptions import ApiError
from dropbox.files import CommitInfo, DeleteError, UploadSessionCursor
from loguru import logger
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from functools import wraps

from objects import MB, get_env


class DropBox:
    """
    Dropbox client.
    Requires key, secret and refresh token.
    """
    _auth_url = "https://api.dropbox.com/oauth2/token"

    def __init__(self, storage_time: float = 1800):
        self._client: dropbox.Dropbox
        self._token: str
        self._token_timer: float = 0
        self._storage: dict[str, float] = {}
        self._storage_time = storage_time

        self._refresh_token = get_env().get("DROPBOX_REFRESH_TOKEN")
        self._app_key = get_env().get("DROPBOX_APP_KEY")
        self._secret = get_env().get("DROPBOX_APP_SECRET")

        self.semaphore = asyncio.Semaphore(20)
        self.pool = ThreadPoolExecutor(max_workers=20)

    @staticmethod
    def _async_wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):  # noqa ANN202
            async with self.semaphore:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(self.pool, lambda: func(self, *args, **kwargs))

        return wrapper

    def _refresh_access_token(self):
        """
        Refreshes access token each 4 hours using
        - refresh_token
        - app key
        - app secret
        :return:
        """
        if time.time() - self._token_timer > 4 * 55 * 60:
            try:
                response = requests.post(url=self._auth_url,
                                         data={
                                             "refresh_token": self._refresh_token,
                                             "grant_type": "refresh_token",
                                             "client_id": self._app_key,
                                             "client_secret": self._secret
                                         },
                                         timeout=5,
                                         )
                oauth_result = response.json()
                self._token = oauth_result.get("access_token")
                self._token_timer = time.time()
                self._client = dropbox.Dropbox(self._token)
                logger.info(f"Successfully get an access token for appkey:{self._app_key}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"Unable to refresh access token for appkey:{self._app_key}: {e.__repr__()}")

    def __enter__(self):
        self._refresh_access_token()
        logger.info(f"Dropbox client appkey:{self._app_key} started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()
        logger.info(f"Dropbox client appkey:{self._app_key} closed")

    @_async_wrap
    def upload(self, local_path: Path) -> str | None:
        """
        Uploads local file to DropBox
        :param local_path: full path to local file
        :return: shared link to DB file | None
        """
        self._refresh_access_token()
        try:
            if local_path.name not in self._storage:
                if local_path.stat().st_size > 140 * MB:  # TODO hardcode
                    self._upload_by_chunks(local_path)
                else:
                    with local_path.open("rb") as f:
                        self._client.files_upload(f=f.read(), path=f"/{local_path.name}")
                self._storage[local_path.name] = time.time()
                logger.info(f"File uploaded to appkey:{self._app_key} {local_path.name}")
                return self._client.sharing_create_shared_link_with_settings(f"/{local_path.name}").url

            logger.info(f"File already in appkey:{self._app_key} {local_path.name}, updating timer")
            self._storage[local_path.name] = time.time()
            shared_links = self._client.sharing_list_shared_links(f"/{local_path.name}")
            if shared_links.links:
                return shared_links.links[0].url
            else:
                logger.error(f"File already in appkey:{self._app_key} but link is unavailable")

        except Exception as e:
            logger.error(f"An exception occurred uploading to appkey:{self._app_key}, {local_path.name} {e.__repr__()}")

    def _upload_by_chunks(self, local_path: Path, chunk_size: int = 16 * MB):
        with local_path.open(mode="rb") as f:
            logger.info(
                f"Upload session started for appkey:{self._app_key}, {local_path.name}, total size {local_path.stat().st_size / MB:.2f} MB")
            uss_result = self._client.files_upload_session_start(f.read(chunk_size))
            session_id = uss_result.session_id
            cursor = UploadSessionCursor(session_id=session_id, offset=f.tell())
            while 1:
                data = f.read(chunk_size)
                if not data:
                    break
                self._client.files_upload_session_append_v2(data, cursor)
                cursor.offset += len(data)

            self._client.files_upload_session_finish(f.read(0), cursor, CommitInfo(path=f"/{local_path.name}"))
            logger.info(f"Upload session ended for appkey:{self._app_key}, {local_path.name}")

    @_async_wrap
    def timer_delete(self):
        keys_to_delete = []
        for file in self._storage:
            if time.time() - self._storage[file] > self._storage_time:
                logger.info(f"Found expired file {file}, appkey:{self._app_key}")
                self.delete(file)
                keys_to_delete.append(file)
        for file in keys_to_delete:
            self._storage.pop(file, None)

    def delete(self, filename: str):
        self._refresh_access_token()
        try:
            self._client.files_delete_v2(f"/{filename}")
            logger.info(f"File successfully deleted: {filename}, appkey:{self._app_key}")
        except (DeleteError, ApiError) as e:
            logger.error(f"An exception occurred deleting {filename} for appkey:{self._app_key} {e.__repr__()}")

    def empty(self) -> bool:
        return len(self._storage) == 0

    @_async_wrap
    def list_dropbox_files(self) -> list[str]:
        """
        Get the list of actually loaded to DP files
        :return: list of file names
        """
        self._refresh_access_token()
        files = []
        result = self._client.files_list_folder("")
        for entry in result.entries:
            files.append(entry.name)
        return files

    def list_storage_files(self) -> list[str]:
        """
        Get the list of stored files using only internal storage dict
        :return: list of file names
        """
        return [file for file in self._storage]

    @_async_wrap
    def storage_space(self) -> float:
        self._refresh_access_token()
        try:
            space = self._client.users_get_space_usage()
            alc = space.allocation
            allocated_space = alc.get_individual().allocated if alc.is_individual() else alc.get_team().allocated
            logger.info(f"appkey:{self._app_key} space: {(allocated_space - space.used) / MB:.2f} MB")
            return (allocated_space - space.used) / MB
        except Exception as e:
            f"Exception occurred trying to get remaining appkey:{self._app_key} space: {e.__repr__()}"
        return 0
