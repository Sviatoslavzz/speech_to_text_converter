from aiogram.filters import Filter
from aiogram.types import Message


class MainButtonFilter(Filter):
    def __init__(self, v: list[str]) -> None:
        self.v = v

    async def __call__(self, message: Message) -> bool:
        return message.text in self.v
