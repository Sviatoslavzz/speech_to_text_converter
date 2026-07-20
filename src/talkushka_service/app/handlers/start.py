from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from talkushka_service.app.db_operation import create_user, get_lc
from talkushka_service.app.keyboards import main_menu
from talkushka_service.app.replies import limits_info_message, welcome_message
from talkushka_service.config.settings import settings

cmd_start_router = Router()


@cmd_start_router.message(CommandStart())
async def command_start_handler(message: Message):
    """
    Receives messages with `/start` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/START")
    lc_ = await get_lc(message)
    await message.answer(welcome_message[lc_], reply_markup=main_menu[lc_])
    await message.answer(
        limits_info_message[lc_].format(
            video_limit=settings.VIDEO_LIMIT,
            audio_limit=settings.AUDIO_LIMIT,
            subtitle_limit=settings.SUBTITLE_LIMIT,
            transcription_limit=settings.TRANSCRIPTION_LIMIT,
            reset_hour=settings.UPDATE_LIMIT_HOUR_UTC + 4,
        )
    )
    await create_user(message)
