import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from loguru import logger

from app.handlers import router
from objects import SERVER, get_env


async def main() -> None:
    session = None
    bot_token = "TG_BOT_TOKEN"
    if SERVER == "local":
        bot_token = "LOCAL_BOT_TOKEN"
        local_server = TelegramAPIServer.from_base("http://localhost:9090")
        session = AiohttpSession(api=local_server)

    bot = Bot(token=get_env().get(bot_token), session=session)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start polling: {e.__repr__()}")
        raise e
    finally:
        await bot.session.close()
        logger.info("Bot session closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.warning(f"Turning off {e.__repr__()}")
