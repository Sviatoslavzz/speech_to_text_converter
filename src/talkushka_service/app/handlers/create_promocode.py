from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from talkushka_service.app.db_operation import create_new_promocode, get_lc, is_able_to_create_promocode
from talkushka_service.app.keyboards import create_promocode, get_subscription_type_as_kb
from talkushka_service.app.replies import (
    choose_promocode_subscription_type,
    choose_promocode_total_use,
    create_promocode_msg,
    custom_promocode,
    promocode_create_fail,
    promocode_create_success,
)
from talkushka_service.app.states import PromocodeRoute
from talkushka_service.db.model import SubscriptionType
from talkushka_service.utils.functions import generate_promocode

create_promocode_router = Router()


@create_promocode_router.message(Command("create_promocode"))
async def command_create_promocode_handler(message: Message):
    """
    Only admins can create promocodes.
    Do not register this command in bot.
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/CREATE_PROMOCODE")
    if await is_able_to_create_promocode(message.from_user.id):
        lc = await get_lc(message)
        await message.answer(create_promocode_msg[lc], reply_markup=create_promocode[lc])


@create_promocode_router.callback_query(F.data == "create_custom_promocode")
async def create_custom_promocode_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:create_custom_promocode")
    lc = await get_lc(callback)
    await callback.message.answer(custom_promocode[lc])
    await state.set_state(PromocodeRoute.custom)


@create_promocode_router.message(PromocodeRoute.custom)
async def custom_promocode_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:state:custom_promocode")
    await state.update_data(promocode=message.text)
    lc = await get_lc(message)
    await message.answer(choose_promocode_subscription_type[lc], reply_markup=get_subscription_type_as_kb())


@create_promocode_router.callback_query(F.data == "generate_promocode")
async def generate_promocode_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:generate_promocode")
    await state.update_data(promocode=generate_promocode())
    lc = await get_lc(callback)
    await callback.message.answer(choose_promocode_subscription_type[lc], reply_markup=get_subscription_type_as_kb())


@create_promocode_router.callback_query(F.data.in_([f"{s_type.name}_{s_type.value}" for s_type in SubscriptionType]))
async def promocode_subscription_type_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:promocode_subscription_type")
    await state.update_data(subscription_type=SubscriptionType[callback.data.split("_")[0]])
    lc = await get_lc(callback)
    await callback.message.answer(choose_promocode_total_use[lc])
    await state.set_state(PromocodeRoute.total_use)


@create_promocode_router.message(PromocodeRoute.total_use)
async def promocode_total_use_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:state:promocode_total_use")
    lc = await get_lc(message)
    try:
        total_use = int(message.text)
        data = await state.get_data()
        if not await create_new_promocode(data["promocode"], total_use, data["subscription_type"]):
            raise ValueError
        await message.answer(promocode_create_success[lc].format(code=data["promocode"]))
    except (ValueError, KeyError):
        await message.answer(promocode_create_fail[lc])
    finally:
        await state.clear()
