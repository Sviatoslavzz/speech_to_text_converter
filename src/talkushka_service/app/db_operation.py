import asyncio

from aiogram.types import CallbackQuery, Message
from loguru import logger

from talkushka_service.app.replies import (
    get_subscription_message,
    promocode_not_found,
    promocode_success,
    promocode_worse_subscription,
)
from talkushka_service.config.settings import settings
from talkushka_service.db.dao import PromocodeDAO, SubscriptionDAO, UserDAO, UserLimitDAO
from talkushka_service.db.model import Privilege, SubscriptionType
from talkushka_service.model.objects import AppOperation


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


async def validate_limit(user_id: int, parameter: AppOperation) -> bool:
    """
    Validate the limit for specific app operation represented by parameter.
    """
    user = await UserLimitDAO.get_one_or_none(user_id=user_id)
    return bool(user and getattr(user, parameter.value, 0) > 0)


async def decrease_limit(user_id: int, parameter: AppOperation, value: int):
    """
    Decreases limit for chosen parameter by value.
    Checks for user privilege and subscription.
    """
    user = await UserDAO.get_one_or_none(user_id=user_id)
    if user and user.privilege == Privilege.user and not user.subscription_id:
        await UserLimitDAO.decrease_limit_by_user_id(user_id=user_id, **{parameter.value: value})


async def apply_promocode(msg: Message | CallbackQuery, language_code: str):
    user = await UserDAO.get_one_or_none(user_id=msg.from_user.id)
    if not user:
        logger.warning("No users found to apply promocode user_id={user_id}", user_id=msg.from_user.id)
        return

    if promocode := await PromocodeDAO.get_one_or_none(code=msg.text):
        if user.subscription_id and \
                (subscription := await SubscriptionDAO.get_one_or_none(id=user.subscription_id)):
            logger.debug("found active subscription for user={user_id}", user_id=msg.from_user.id)
            if subscription.type.value >= promocode.type.value:
                logger.info("try to apply promocode with type worse than actual subscription user_id={user_id}",
                            user_id=msg.from_user.id)
                await msg.answer(promocode_worse_subscription[language_code])
                return

        if promocode.actual_use < promocode.total_use:
            asyncio.create_task(PromocodeDAO.update_by_kwargs(id=promocode.id, actual_use=promocode.actual_use + 1))
            new_subscription = await SubscriptionDAO.add_by_kwargs(type=promocode.type)
            asyncio.create_task(UserDAO.update_by_kwargs(user_id=user.user_id, subscription_id=new_subscription.id))
            logger.info("subscription {type} is applied for user_id={user_id} by promocode",
                        type=promocode.type,
                        user_id=msg.from_user.id)
            await msg.answer(promocode_success[language_code].format(
                subscription=get_subscription_message(new_subscription.type, language_code))
            )
            return

    await msg.answer(promocode_not_found[language_code])


async def update_user_limits():
    await UserLimitDAO.reset_limits(
        video=settings.VIDEO_LIMIT,
        audio=settings.AUDIO_LIMIT,
        subtitle=settings.SUBTITLE_LIMIT,
        transcription=settings.TRANSCRIPTION_LIMIT
    )


async def check_subscription() -> list[tuple[int, str]]:
    """
    Checks user subscription.
    :return: list of user ids with deactivated subscriptions.
    """

    return await UserDAO.remove_subscriptions(subscription_ids=await SubscriptionDAO.deactivate_expired())


async def is_able_to_create_promocode(user_id: int) -> bool:
    user = await UserDAO.get_one_or_none(user_id=user_id)
    return bool(user and user.privilege == Privilege.admin)


async def create_new_promocode(code: str, total_use: int, subscription_type: SubscriptionType) -> bool:
    new_promocode = await PromocodeDAO.add_by_kwargs(code=code, total_use=total_use, type=subscription_type)
    return bool(new_promocode)
