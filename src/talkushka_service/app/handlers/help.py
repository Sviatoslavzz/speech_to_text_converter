import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from talkushka_service.app.db_operation import change_user_lc, get_helpdesk_chats, get_lc
from talkushka_service.app.keyboards import approve_menu, change_language_menu, help_menu, main_menu
from talkushka_service.app.replies import (
    cancel_reply,
    change_language_reply,
    contact_helpdesk_reply,
    help_reply,
    helpdesk_mess,
    helpdesk_sent_reply,
    language_changed,
    validate_helpdesk_message_reply,
)
from talkushka_service.app.states import HelpRoute

cmd_help_router = Router()


@cmd_help_router.message(Command("help"))
async def command_help_handler(message: Message):
    """
    Receives messages with `/help` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/HELP")
    lc_ = await get_lc(message)
    await message.answer(help_reply[lc_], reply_markup=help_menu[lc_])


@cmd_help_router.callback_query(F.data == "change_language")
async def change_language_handler(callback: CallbackQuery):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:change_language")
    lc_ = await get_lc(callback)
    sent = await callback.message.answer(change_language_reply[lc_].format(lc=lc_),
                                         reply_markup=change_language_menu[lc_])
    await asyncio.sleep(10)
    await sent.delete()


@cmd_help_router.callback_query(F.data.in_(["lc_to_ru", "lc_to_en"]))
async def change_language_handler_2(callback: CallbackQuery):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:change_language_2")
    lc_ = await change_user_lc(callback, callback.data)
    await callback.message.answer(language_changed[lc_], reply_markup=main_menu[lc_])


@cmd_help_router.callback_query(F.data == "contact_helpdesk")
async def contact_helpdesk_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:contact_helpdesk")
    await callback.message.answer(contact_helpdesk_reply[await get_lc(callback)])
    await state.set_state(HelpRoute.validation)


@cmd_help_router.message(HelpRoute.validation)
async def helpdesk_validation_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:helpdesk_validation")
    lc_ = await get_lc(message)
    await message.answer(validate_helpdesk_message_reply[lc_].format(r=message.text),
                         reply_markup=approve_menu[lc_])
    await state.update_data(validation=message.text)
    await state.set_state(HelpRoute.approve)


@cmd_help_router.callback_query(F.data == "approve", HelpRoute.approve)
async def approve_helpdesk_request_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:approve_helpdesk_request")
    await callback.message.answer(helpdesk_sent_reply[await get_lc(callback)])
    state_data = await state.get_data()

    for chat_id in await get_helpdesk_chats():
        await callback.bot.send_message(chat_id,
                                        helpdesk_mess.format(un=callback.from_user.username,
                                                             uid=callback.from_user.id) + \
                                        state_data.get("validation", ""))
    await state.clear()


@cmd_help_router.callback_query(F.data == "cancel", HelpRoute.approve)
async def cancel_helpdesk_request_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:cancel_helpdesk_request")
    await callback.message.answer(cancel_reply[await get_lc(callback)])
    await state.clear()
