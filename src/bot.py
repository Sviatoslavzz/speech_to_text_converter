import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from loguru import logger

from app.handlers import router
from app_worker import AppWorker
from config.base import YAMLConfig
from config.conf_models import BotConfig
from parser import get_parser


async def start_bot(bot_conf: BotConfig):
    session = None
    if bot_conf.server == "local":
        local_server = TelegramAPIServer.from_base(f"http://{bot_conf.host}:{bot_conf.port}")
        session = AiohttpSession(api=local_server)

    bot = Bot(token=bot_conf.token_env, session=session)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start polling: {e.__repr__()}")
    finally:
        await bot.session.close()
        logger.info("Bot session closed.")


async def main() -> None:
    parser = get_parser()
    args = parser.parse_args()
    config: YAMLConfig = args.config

    AppWorker(config.data)

    await start_bot(config.data.bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.warning(f"Turning off {e.__repr__()}")
