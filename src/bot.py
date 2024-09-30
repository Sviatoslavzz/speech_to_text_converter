import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from loguru import logger

from app.handlers import router

def get_env() -> dict[str, str]:
    load_dotenv()
    return {"YOUTUBE_API": os.getenv("YOUTUBE_API"), "TOKEN": os.getenv("TOKEN")}

async def main() -> None:
    bot = Bot(token=get_env().get("TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt")
