import time
from dataclasses import dataclass
from pathlib import Path
from typing import Type

from loguru import logger
from objects import DownloadTask, MINUTE
from storage.dropbox_storage import DropBox


@dataclass(slots=True)
class Storage:
    cls: Type[DropBox]
    space: int = 0


class StorageWorker:
    """
    Singleton worker
    Receives storage classes
    Initializes them and fairly distributes files bw them
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, storage_time: float = 30 * MINUTE):
        logger.info(f"{self.__class__.__name__}: Initializing...")
        self.storages = [Storage(cls=DropBox)]
        self._connected = False
        self.storage_time = storage_time
        self._initialize_storages()
        self.timer = time.time()

    @classmethod
    def get_instance(cls):
        return cls._instance

    def _initialize_storages(self):
        for i in range(len(self.storages)):
            self.storages[i].cls = self.storages[i].cls(storage_time=self.storage_time)
            self.storages[i].cls.start()
        self._connected = True
        logger.info(f"{self.__class__.__name__} started {len(self.storages)} storages.")

    def connect_storages(self):
        if not self._connected:
            for storage in self.storages:
                if not storage.cls.is_connected():
                    storage.cls.start()
            self._connected = True

    def stop_storages(self):
        if self._connected:
            for storage in self.storages:
                if storage.cls.is_connected():
                    storage.cls.stop()
            self._connected = False
            logger.info(f"{self.__class__.__name__} stopped {len(self.storages)} storages.")

    def is_connected(self):
        return self._connected

    async def upload(self, local_path: Path) -> str | None:
        """
        Checks if any storage has the same file uploaded
        Uploads the file to the most sutable storage
        :param local_path: path to file
        :return: storage link | None
        """
        for storage in self.storages:
            if local_path.name in storage.cls.list_storage_files():
                return await storage.cls.upload(local_path)

        return await self.storages[0].cls.upload(local_path)

    async def update_space(self):
        """
        Updates available space for each storage
        """
        for storage in self.storages:
            storage.space = await storage.cls.storage_space()
        sorted(self.storages, key=lambda x: x.space, reverse=True)

    async def check_timer(self):
        """
        Sends timer-delete request to each storage every minute
        Assumed to be called constantly
        """
        if time.time() - self.timer > MINUTE:
            for storage in self.storages:
                await storage.cls.timer_delete()
            await self.update_space()
            self.timer = time.time()


async def storage_worker_as_target(task: DownloadTask | None = None) -> DownloadTask | None:
    sw = StorageWorker.get_instance()
    if not sw:
        sw = StorageWorker(storage_time=60)  # TODO storage time from conf?
        await sw.update_space()

    if task and task.local_path:
        task.storage_link = await sw.upload(task.local_path)
        return task

    await sw.check_timer()
    return None
