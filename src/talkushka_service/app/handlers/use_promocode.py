from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from talkushka_service.app.db_operation import apply_promocode, get_lc
from talkushka_service.app.replies import promocode
from talkushka_service.app.states import PromocodeRoute

use_promocode_router = Router()


@use_promocode_router.message(Command("promocode"))
async def command_promocode_handler(message: Message, state: FSMContext):
    """
    Receives messages with `/promocode` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/PROMOCODE")
    lc = await get_lc(message)
    await message.answer(promocode[lc])
    await state.set_state(PromocodeRoute.receive)


@use_promocode_router.message(PromocodeRoute.receive)
async def promocode_validation_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:promocode_validation")
    lc = await get_lc(message)
    await apply_promocode(message, lc)
    await state.clear()
