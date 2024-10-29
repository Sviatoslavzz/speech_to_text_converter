import asyncio
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from typing import Any

import dropbox
import requests
from dropbox.files import CommitInfo, UploadSessionCursor
from loguru import logger

from config import DropboxConfig
from objects import HOUR, MB, MINUTE


class DropBox:
    """
    Dropbox client.
    Requires key, secret and refresh token.
    Saves files to storage and set timer for keeping it.
    Once timer is out removes file from storage (requires call)
    """

    _auth_url = "https://api.dropbox.com/oauth2/token"

    def __init__(self, config: DropboxConfig):
        self._client: dropbox.Dropbox | None = None
        self._token: str | None = None
        self._token_timer: float = 0
        self._storage: dict[str, float] = {}
        self._storage_time = config.storage_time
        self._connected = False

        self._refresh_token = config.refresh_token
        self._app_key = config.app_key
        self._secret = config.app_secret
        self.check_auth_tokens()

        self.pool = ThreadPoolExecutor(max_workers=20)

    def check_auth_tokens(self) -> None:
        if not (self._refresh_token and self._app_key and self._secret):
            logger.error(f"{self.__class__.__name__} accepts exactly 3 tokens: refresh_token, app_key, secret")
            raise Exception(f"{self.__class__.__name__} accepts exactly 3 tokens: refresh_token, app_key, secret")

    @staticmethod
    def _async_wrap(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):  # ANN202
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self.pool, lambda: func(self, *args, **kwargs))

        return wrapper

    def _refresh_access_token(self):
        """
        Refreshes access token each 4 hours using
        - refresh_token
        - app key
        - app secret
        """
        if time.time() - self._token_timer > (3 * HOUR + 50 * MINUTE) or not self._connected:
            try:
                response = requests.post(
                    url=self._auth_url,
                    data={
                        "refresh_token": self._refresh_token,
                        "grant_type": "refresh_token",
                        "client_id": self._app_key,
                        "client_secret": self._secret,
                    },
                    timeout=5,
                )
                oauth_result = response.json()
                self._token = oauth_result.get("access_token")
                self._token_timer = time.time()
                logger.info(f"Successfully get an access token for appkey:{self._app_key}")
                if self._connected:
                    self._client.close()
                    self.start()
            except requests.exceptions.HTTPError as e:
                logger.error(f"Unable to refresh access token for appkey:{self._app_key}: {e.__repr__()}")

    def start(self):
        if not self._connected:
            self._refresh_access_token()
        self._client = dropbox.Dropbox(self._token)
        logger.info(f"Dropbox client appkey:{self._app_key} connected")
        self._connected = True

    def stop(self):
        if self._connected:
            self._client.close()
            self._client = None
            logger.info(f"Dropbox client appkey:{self._app_key} disconnected")
            self._connected = False

    def is_connected(self):
        return self._connected

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
            logger.error(f"File already in appkey:{self._app_key} but link is unavailable")
        except Exception as e:
            logger.error(f"An exception occurred uploading to appkey:{self._app_key}, {local_path.name} {e.__repr__()}")
            raise Exception(f"Unable to upload file: {local_path.name}") from e

    def _upload_by_chunks(self, local_path: Path, chunk_size: int = 16 * MB):
        with local_path.open(mode="rb") as f:
            logger.info(f"""
            Upload session started for appkey:{self._app_key},
{local_path.name}, total size {local_path.stat().st_size / MB:.2f} MB""")
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
        for file in list(self._storage):
            if self._storage.get(file, False) and time.time() - self._storage[file] > self._storage_time:
                logger.info(f"Found expired file {file}, appkey:{self._app_key}")
                self._storage.pop(file, None)
                self.delete(file)

    def delete(self, filename: str):
        self._refresh_access_token()
        try:
            self._client.files_delete_v2(f"/{filename}")
            logger.info(f"File successfully deleted: {filename}, appkey:{self._app_key}")
        except Exception as e:
            logger.error(f"An exception occurred deleting {filename} for appkey:{self._app_key} {e.__repr__()}")

    def empty(self) -> bool:
        return not self._storage

    @_async_wrap
    def list_dropbox_files(self) -> list[str]:
        """
        Get the list of actually loaded to DP files
        :return: list of file names
        """
        self._refresh_access_token()
        result = self._client.files_list_folder("")
        return [entry.name for entry in result.entries]

    def list_storage_files(self) -> list[str]:
        """
        Get the list of stored files using only internal storage dict
        :return: list of file names
        """
        return list(self._storage)

    @_async_wrap
    def storage_space(self) -> float:
        self._refresh_access_token()
        try:
            space = self._client.users_get_space_usage()
            alc = space.allocation
            allocated_space = alc.get_individual().allocated if alc.is_individual() else alc.get_team().allocated
            logger.info(f"appkey:{self._app_key} space: {(allocated_space - space.used) / MB:.2f} MB")
            return allocated_space - space.used
        except Exception as e:
            logger.error(f"Exception occurred trying to get remaining space. appkey:{self._app_key} {e.__repr__()}")
        return 0
