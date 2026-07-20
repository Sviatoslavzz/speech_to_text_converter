import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from functools import wraps
from pathlib import Path
from ssl import Purpose, SSLContext, create_default_context
from time import time
from typing import Any

import aiofiles
import aiofiles.os
from grpclib.client import Channel
from loguru import logger

from talkushka_service.config.models import GrpcConfig
from talkushka_service.model.objects import MB, MINUTE
from talkushka_service.proto_gen.whisper import AudioChunk, AudioTransferStub, HealthCheckRequest
from talkushka_service.utils.functions import get_project_root


class GrpcClient:
    def __init__(self, config: GrpcConfig):
        self.config = config
        self.__whisper_channel = None
        self.__whisper_stub: AudioTransferStub | None = None
        self.__use_time = time()
        self.__connected = False
        asyncio.get_running_loop().create_task(self.__client_timer_coro())

        logger.debug("{cls} initialized", cls=self.__class__.__name__)

    @staticmethod
    def __get_ssl_context() -> SSLContext:
        """
        Create and configure an SSL context for the gRPC client.
        """
        try:
            cert_path = get_project_root() / "cert/talkushka-transcriber"
            ssl_context = create_default_context(Purpose.SERVER_AUTH)
            ssl_context.load_verify_locations(cafile=cert_path / "ca.crt")
            ssl_context.load_cert_chain(certfile=cert_path / "client.crt", keyfile=cert_path / "client.key")
        except Exception as e:
            logger.error("Failed to configure SSL context: {err}", err=e.__repr__())
            raise e

        return ssl_context

    async def __connect(self):
        try:
            if not self.__connected:
                self.__whisper_channel = Channel(
                    host=self.config.host, port=self.config.port, ssl=self.__get_ssl_context()
                )
                self.__whisper_stub = AudioTransferStub(self.__whisper_channel)
                self.__connected = await self.is_whisper_connected()
                logger.info("Connected to gRPC {host}:{port}", host=self.config.host, port=self.config.port)
        except Exception as e:
            logger.error("Failed to connect to 'whisper_service' GRPC server: {err}", err=e.__repr__())
            self.__disconnect()

    def __disconnect(self):
        if self.__whisper_channel:
            self.__whisper_channel.close()
            logger.info("Disconnected from gRPC {host}:{port}", host=self.config.host, port=self.config.port)
        self.__whisper_stub = None
        self.__connected = False

    async def __client_timer_coro(self):
        await self.__connect()
        self.__use_time = time()
        while True:
            if self.__connected and time() - self.__use_time > self.config.channel_idle_time * MINUTE:
                self.__disconnect()
                break
            if not self.__connected:
                break
            await asyncio.sleep(15)

    @staticmethod
    def __update_timer(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if self.__connected:
                self.__use_time = time()
            else:
                asyncio.create_task(self.__client_timer_coro())
            return await func(self, *args, **kwargs)

        return wrapper

    @__update_timer
    async def stream_audio_file(self, path_: Path) -> tuple[bool, Path | None]:
        """
        Streams audio file to grpc Server of 'talkushka-transcriber' service
        """

        async def generate_chunks() -> AsyncIterator[AudioChunk]:
            logger.debug("Generating chunks for sending to gRPC whisper server")
            nonlocal path_
            async with aiofiles.open(path_, "rb") as audio_file:
                while True:
                    chunk_data = await audio_file.read(MB)
                    if not chunk_data:
                        break
                    yield AudioChunk(
                        payload=chunk_data,
                    )
            logger.debug("Chunks are successfully sent to gRPC whisper server")

        res = False
        async with aiofiles.open(path_.with_suffix(".txt"), "wb") as text_file:
            async for message in self.__whisper_stub.stream_audio(generate_chunks()):
                if message.result:
                    res = message.result
                    await text_file.write(message.payload)

        await aiofiles.os.unlink(path_)
        if not res:
            await aiofiles.os.unlink(path_.with_suffix(".txt"))

        return res, path_.with_suffix(".txt") if res else None

    async def is_whisper_connected(self):
        """
        Health check request to gRPC whisper server
        Raises: OSerror in case of missing connection
        Returns: boolean response from gRPC server
        """
        resp = await self.__whisper_stub.health_check(HealthCheckRequest("check"))
        return resp.answer

    @property
    async def connected(self):
        if not self.__connected:
            asyncio.create_task(self.__client_timer_coro())
            await asyncio.sleep(1)
        return self.__connected
