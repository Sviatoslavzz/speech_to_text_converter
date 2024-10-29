import time
from asyncio import sleep
from dataclasses import dataclass

from loguru import logger

from config import DropboxConfig
from objects import MINUTE, DownloadTask, get_env
from storage.dropbox_storage import DropBox


@dataclass(slots=True)
class Storage:
    cls: DropBox
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

    def __init__(self, config: list[DropboxConfig]):
        logger.info(f"{self.__class__.__name__}: Initializing...")
        self.storages = [Storage(cls=storage_conf.cls(storage_conf)) for storage_conf in config]
        self._connected = False
        self._initialize_storages()
        self.timer = time.time()

    @classmethod
    def get_instance(cls):
        return cls._instance

    def _initialize_storages(self):
        for i in range(len(self.storages)):
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

    async def upload(self, task: DownloadTask):
        """
        Checks if any storage has the same file uploaded
        Uploads the file to the most sutable storage
        :param task: DownloadTask
        :return: storage link | None
        """

        """Check if any storage has the same file uploaded then just return  its link"""
        for storage in self.storages:
            if task.local_path.name in storage.cls.list_storage_files():
                task.storage_link = await storage.cls.upload(task.local_path)
                task.local_path.unlink(missing_ok=True)
                return

        if task.file_size > self.storages[0].space:
            task.message.message["ru"] = "К сожалению, нет места во внешнем хранилище"
            task.result = False
        else:
            try:
                task.storage_link = await self.storages[0].cls.upload(task.local_path)
                task.local_path.unlink(missing_ok=True)
            except Exception:
                task.message.message["ru"] = "Не получилось загрузить файл во внешнее хранилище."
                task.result = False

        task.local_path.unlink(missing_ok=True)

    async def update_space(self):
        """
        Updates available space for each storage
        """
        for storage in self.storages:
            storage.space = await storage.cls.storage_space()
        self.storages = sorted(self.storages, key=lambda x: x.space, reverse=True)

    async def check_timer(self):
        """
        Sends timer-delete request to each storage every minute
        Assumed to be called constantly
        """
        if time.time() - self.timer > MINUTE:
            self.timer = time.time()
            for storage in self.storages:
                if not storage.cls.empty():
                    await storage.cls.timer_delete()
            await self.update_space()


async def storage_worker_as_target(task: DownloadTask | None = None) -> DownloadTask | None:
    sw = StorageWorker.get_instance()
    if not sw:
        # TODO вынести отсюда наверх - передавать каждый раз как аргумент
        conf = [
            DropboxConfig(
                cls=DropBox,
                refresh_token=get_env().get("DROPBOX_REFRESH_TOKEN"),
                app_key=get_env().get("DROPBOX_APP_KEY"),
                app_secret=get_env().get("DROPBOX_APP_SECRET"),
            ),
            DropboxConfig(
                cls=DropBox,
                refresh_token=get_env().get("DROPBOX_REFRESH_TOKEN_2"),
                app_key=get_env().get("DROPBOX_APP_KEY_2"),
                app_secret=get_env().get("DROPBOX_APP_SECRET_2"),
            ),
        ]
        sw = StorageWorker(conf)
        await sleep(1)
        await sw.update_space()

    if task and task.local_path:
        await sw.upload(task)
        return task

    await sw.check_timer()
    return None
