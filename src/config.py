from dataclasses import dataclass
from typing import TypeVar

from objects import MINUTE

T = TypeVar("T")


@dataclass(slots=True)
class DropboxConfig:
    cls: type[T]
    storage_time: float = 5 * MINUTE
    refresh_token: str | None = None
    app_key: str | None = None
    app_secret: str | None = None
