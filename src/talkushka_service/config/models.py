from functools import partial
from os import getenv
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

from talkushka_service.config.factory import get_storage_cls
from talkushka_service.objects import MINUTE
from talkushka_service.utils import create_saving_dir, validate_db_storages

storage_class = TypeVar("storage_class")  # Todo bound to abstract storage


class DropboxConfig(BaseModel):
    cls: type[storage_class] | None = Field(default_factory=partial(get_storage_cls, "DropBox"),
                                            title="Storage class",
                                            description="DropBox")
    storage_time: float | None = Field(default=5 * MINUTE, title="Storage time in minutes")
    refresh_token_env: str = Field(..., title="Environment variable name")
    app_key_env: str = Field(..., title="Environment variable name")
    app_secret_env: str = Field(..., title="Environment variable name")

    @field_validator("cls", mode="before")
    @classmethod
    def __validate_cls(cls, value) -> type[storage_class]:
        return get_storage_cls(value)

    @field_validator("storage_time", mode="before")
    @classmethod
    def __validate_storage_time(cls, value) -> type[storage_class]:
        return value * MINUTE

    @field_validator("refresh_token_env", mode="before")
    @classmethod
    def __validate_refresh_token(cls, value) -> str:
        if not getenv(value):
            raise AssertionError(f"There is no environment variable '{value}'")
        return getenv(value)

    @field_validator("app_key_env", mode="before")
    @classmethod
    def __validate_app_key(cls, value) -> str:
        if not getenv(value):
            raise AssertionError(f"There is no environment variable '{value}'")
        return getenv(value)

    @field_validator("app_secret_env", mode="before")
    @classmethod
    def __validate_app_secret(cls, value) -> str:
        if not getenv(value):
            raise AssertionError(f"There is no environment variable '{value}'")
        return getenv(value)


class StorageConfig(BaseModel):
    q_size: int | None = Field(500, title="Process executor queue size")
    storages: dict[str, DropboxConfig] | None = Field(None, title="Storages")

    @field_validator("storages", mode="before")
    @classmethod
    def validate_storages(cls, value) -> dict[str, DropboxConfig]:
        if isinstance(value, list):
            return {list(item.keys())[0]: DropboxConfig(**list(item.values())[0]) for item in value}
        raise AssertionError("Invalid format for storages")

    @model_validator(mode="after")
    def verify_storage_config(self):
        if self.storages and len(self.storages) > 1:
            validate_db_storages(list(self.storages.values()))

        return self


class BotConfig(BaseModel):
    server: str = Field("telegram", title="Telegram bot server", description="local | telegram")
    host: str | None = Field(None, title="Server host")
    port: int | None = Field(None, title="Server port")
    token_env: str = Field(..., title="Environment variable name")

    @field_validator("token_env", mode="before")
    @classmethod
    def validate_token_env(cls, value) -> str:
        if not getenv(value):
            raise ValueError(f"There is no environment variable '{value}'")
        return getenv(value)

    @model_validator(mode="after")
    def validate_bot_config(self):
        if self.server == "local" and (not self.host or not self.port):
            raise ValueError("Bot host and port must be set in local mode")
        return self


class YouTubeConfig(BaseModel):
    api_key_env: str = Field(..., title="Environment variable name")
    heavy_pool_size: int | None = Field(20, title="Video | audio download pool size")
    light_pool_size: int | None = Field(40, title="Text download pool size")
    save_dir: Path | None = Field(default_factory=partial(create_saving_dir, "saved_files"),
                                  title="Directory for saving temp files")
    proxies: list[str] | None = Field(None, title="List of proxies")

    @field_validator("api_key_env", mode="before")
    @classmethod
    def validate_api_key(cls, value) -> str:
        if not getenv(value):
            raise ValueError(f"There is no environment variable '{value}'")
        return getenv(value)

    @field_validator("save_dir", mode="before")
    @classmethod
    def validate_save_dir(cls, value) -> Path:
        return create_saving_dir(value)


class GrpcConfig(BaseModel):
    host: str | None = Field("localhost", title="gRPC server host")
    port: int | None = Field(50051, title="gRPC server port")
    channel_idle_time: int | None = Field(10, title="Channel idle time in minutes",
                                          description="time to have channel opened without usage")


class BaseConfig(BaseModel):
    bot: BotConfig
    youtube: YouTubeConfig
    storage: StorageConfig
    grpc: GrpcConfig
