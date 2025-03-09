import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from talkushka_service.app.handlers import router
from talkushka_service.app_worker import AppWorker
from talkushka_service.config.base import YAMLConfig
from talkushka_service.config.logger_settings import logger
from talkushka_service.config.models import BotConfig
from talkushka_service.utils.parser import get_parser


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


async def _run() -> None:
    parser = get_parser()
    args = parser.parse_args()
    config: YAMLConfig = args.config

    worker = AppWorker(config.data)

    await start_bot(config.data.bot)

    worker.stop_executors()


def main():
    try:
        asyncio.run(_run())
    except Exception as e:
        logger.warning(f"Turning off {e.__repr__()}")
