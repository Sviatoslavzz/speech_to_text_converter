from typing import TypeVar
from pydantic import BaseModel, Field, field_validator
from objects import MINUTE
from transcribers.abscract_transcriber import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber

storage_class = TypeVar("storage_class")


class DropboxConfig(BaseModel):
    cls: str = Field(..., title="Storage class", description="DropBox")
    storage_time: float | None = Field(5 * MINUTE, title="Storage time")
    refresh_token_env: str = Field(..., title="Environment variable name")
    app_key_env: str = Field(..., title="Environment variable name")
    app_secret_env: str = Field(..., title="Environment variable name")


class StorageConfig(BaseModel):
    q_size: int | None = Field(500, title="Process executor queue size")
    storages: dict[str, DropboxConfig] = Field(..., title="Storages")

    @field_validator("storages", mode="before")
    def validate_storages(cls, value) -> dict[str, DropboxConfig]:
        if isinstance(value, list):
            return {list(item.keys())[0]: DropboxConfig(**list(item.values())[0]) for item in value}
        raise ValueError("Invalid format for storages")


class BotConfig(BaseModel):
    server: str = Field("telegram", title="Telegram bot server", description="local or telegram")
    host: str | None = Field(None, title="Server host")
    port: int | None = Field(None, title="Server port")
    token_env: str = Field(..., title="Environment variable name")


class YouTubeConfig(BaseModel):
    api_key_env: str = Field(..., title="Environment variable name")
    heavy_pool_size: int | None = Field(20, title="Video | audio download pool size")
    light_pool_size: int | None = Field(40, title="Text download pool size")
    save_dir: str | None = Field("saved_files", title="Directory for saving temp files")
    proxies: list[str] | None = Field(None, title="List of proxies")


class TranscriberConfig(BaseModel):
    q_size: int | None = Field(300, title="Process executor queue size")
    cls: type[AbstractTranscriber] | None = Field("FasterWhisperTranscriber",
                                                  title="Transcriber class",
                                                  description="WhisperTranscriber | FasterWhisperTranscriber")
    model: str | None = Field("small", title="Whisper model")


class BaseConfig(BaseModel):
    bot: BotConfig
    youtube: YouTubeConfig
    transcriber: TranscriberConfig
    storage: StorageConfig
