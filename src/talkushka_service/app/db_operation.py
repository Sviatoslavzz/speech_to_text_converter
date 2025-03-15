from aiogram.types import CallbackQuery, Message
from loguru import logger

from talkushka_service.db.dao import UserDAO, UserLimitDAO
from talkushka_service.db.model import Privilege


async def create_user(message: Message | CallbackQuery):
    if not await UserDAO.get_one_or_none(user_id=message.from_user.id):
        await UserDAO.add_by_kwargs(user_id=message.from_user.id,
                                    chat_id=message.chat.id,
                                    username=message.from_user.username,
                                    lc="ru" if message.from_user.language_code == "ru" else "en")
        await UserLimitDAO.add_by_kwargs(user_id=message.from_user.id)
        logger.info("{user}:{id} added to database", user=message.from_user.username, id=message.from_user.id)


async def get_lc(msg: CallbackQuery | Message):
    """
    Get the language code of the user.
    """
    user = await UserDAO.get_one_or_none(user_id=msg.from_user.id)
    return user.lc if user else ("ru" if msg.from_user.language_code == "ru" else "en")


async def change_user_lc(msg: CallbackQuery | Message, data: str):
    user = await UserDAO.update_by_kwargs(user_id=msg.from_user.id, lc=data.split("_")[-1])
    return user.lc


async def get_helpdesk_chats() -> list[int]:
    users = await UserDAO.get_helpdesk_and_admin()
    return [user.chat_id for user in users]


async def validate_file_transcription_limit(msg: Message | CallbackQuery):
    user = await UserLimitDAO.get_one_or_none(user_id=msg.from_user.id)
    return bool(user and user.transcription > 0)


async def validate_video_download_limit(msg: Message | CallbackQuery):
    user = await UserLimitDAO.get_one_or_none(user_id=msg.from_user.id)
    return bool(user and user.video > 0)


async def validate_audio_download_limit(msg: Message | CallbackQuery):
    user = await UserLimitDAO.get_one_or_none(user_id=msg.from_user.id)
    return bool(user and user.audio > 0)


async def validate_subtitle_download_limit(msg: Message | CallbackQuery):
    user = await UserLimitDAO.get_one_or_none(user_id=msg.from_user.id)
    return bool(user and user.subtitle > 0)


async def decrease_transcription_limit(msg: CallbackQuery | Message):
    user = await UserDAO.get_one_or_none(user_id=msg.from_user.id)
    if user and user.privilege == Privilege.user:
        await UserLimitDAO.decrease_limit_by_user_id(user_id=msg.from_user.id, transcription=1)


async def decrease_video_limit(msg: CallbackQuery | Message):
    user = await UserDAO.get_one_or_none(user_id=msg.from_user.id)
    if user and user.privilege == Privilege.user:
        await UserLimitDAO.decrease_limit_by_user_id(user_id=msg.from_user.id, video=1)


async def decrease_audio_limit(msg: CallbackQuery | Message):
    user = await UserDAO.get_one_or_none(user_id=msg.from_user.id)
    if user and user.privilege == Privilege.user:
        await UserLimitDAO.decrease_limit_by_user_id(user_id=msg.from_user.id, audio=1)


async def decrease_subtitle_limit(msg: CallbackQuery | Message):
    user = await UserDAO.get_one_or_none(user_id=msg.from_user.id)
    if user and user.privilege == Privilege.user:
        await UserLimitDAO.decrease_limit_by_user_id(user_id=msg.from_user.id, subtitle=1)
