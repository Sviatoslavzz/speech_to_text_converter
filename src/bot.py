import asyncio

from aiogram import Bot, Dispatcher
from loguru import logger

from app.handlers import router
from objects import get_env


async def main() -> None:
    bot = Bot(token=get_env().get("TG_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt")
