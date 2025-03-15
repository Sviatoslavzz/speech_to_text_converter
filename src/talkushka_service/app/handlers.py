import asyncio

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions, Message
from loguru import logger

from talkushka_service.app import replies as rp
from talkushka_service.app.db_operation import (
    apply_promocode,
    change_user_lc,
    create_user,
    decrease_limit,
    get_helpdesk_chats,
    get_lc,
    validate_limit,
)
from talkushka_service.app.filters import MainButtonFilter
from talkushka_service.app.keyboards import (
    action_menu,
    approve_menu,
    change_language_menu,
    generate_option_keyboard,
    help_menu,
    main_menu,
    option_chooser_menu,
    proceed_simple_menu,
    standard_video_options_menu,
)
from talkushka_service.app.states import HelpRoute, PromocodeRoute, UserRoute
from talkushka_service.app.support_handlers import (
    check_content_type,
    check_privilege_and_load,
    task_completion_loop,
)
from talkushka_service.app_worker import AppWorker
from talkushka_service.model.objects import (
    AppOperation,
    DownloadTask,
    VideoOptions,
    YouTubeVideo,
)

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    """
    Receives messages with `/start` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/START")
    lc_ = await get_lc(message)
    await message.answer(rp.welcome_message[lc_], reply_markup=main_menu[lc_])
    await create_user(message)


@router.message(Command("help"))
async def command_help_handler(message: Message):
    """
    Receives messages with `/help` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/HELP")
    lc_ = await get_lc(message)
    await message.answer(rp.help_reply[lc_], reply_markup=help_menu[lc_])


@router.message(Command("promocode"))
async def command_promocode_handler(message: Message, state: FSMContext):
    """
    Receives messages with `/promocode` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/PROMOCODE")
    lc_ = await get_lc(message)
    await message.answer(rp.promocode[lc_])
    await state.set_state(PromocodeRoute.receive)

@router.message(PromocodeRoute.receive)
async def promocode_validation_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:promocode_validation")
    lc_ = await get_lc(message)
    await apply_promocode(message, lc_)
    await state.clear()

@router.callback_query(F.data == "change_language")
async def change_language_handler(callback: CallbackQuery):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:change_language")
    lc_ = await get_lc(callback)
    sent = await callback.message.answer(rp.change_language_reply[lc_].format(lc=lc_),
                                         reply_markup=change_language_menu[lc_])
    await asyncio.sleep(10)
    await sent.delete()


@router.callback_query(F.data.in_(["lc_to_ru", "lc_to_en"]))
async def change_language_handler_2(callback: CallbackQuery):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:change_language_2")
    lc_ = await change_user_lc(callback, callback.data)
    await callback.message.answer(rp.language_changed[lc_], reply_markup=main_menu[lc_])


@router.callback_query(F.data == "contact_helpdesk")
async def contact_helpdesk_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:contact_helpdesk")
    await callback.message.answer(rp.contact_helpdesk_reply[await get_lc(callback)])
    await state.set_state(HelpRoute.validation)


@router.message(HelpRoute.validation)
async def helpdesk_validation_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:helpdesk_validation")
    lc_ = await get_lc(message)
    await message.answer(rp.validate_helpdesk_message_reply[lc_].format(r=message.text),
                         reply_markup=approve_menu[lc_])
    await state.update_data(validation=message.text)
    await state.set_state(HelpRoute.approve)


@router.callback_query(F.data == "approve", HelpRoute.approve)
async def approve_helpdesk_request_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:approve_helpdesk_request")
    await callback.message.answer(rp.helpdesk_sent_reply[await get_lc(callback)])
    state_data = await state.get_data()

    for chat_id in await get_helpdesk_chats():
        await callback.bot.send_message(chat_id,
                                        rp.helpdesk_mess.format(un=callback.from_user.username,
                                                                uid=callback.from_user.id) + \
                                        state_data.get("validation", ""))
    await state.clear()


@router.callback_query(F.data == "cancel", HelpRoute.approve)
async def cancel_helpdesk_request_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:cancel_helpdesk_request")
    await callback.message.answer(rp.cancel_reply[await get_lc(callback)])
    await state.clear()


@router.message(MainButtonFilter(rp.choose_video_button.values()))
async def video_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:video_handler")
    lc_ = await get_lc(message)
    await state.update_data(option="video")
    await state.set_state(UserRoute.videos)
    await message.answer(rp.provide_links[lc_])


@router.message(MainButtonFilter(rp.choose_channel_button.values()))
async def channel_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:channel_handler")
    lc_ = await get_lc(message)
    await state.update_data(option="channel")
    await state.set_state(UserRoute.videos)
    await message.answer(rp.provide_channel[lc_])


@router.message(MainButtonFilter(rp.choose_file_button.values()))
async def file_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:file_handler")
    lc_ = await get_lc(message)

    if await validate_limit(message.from_user.id, AppOperation.TRANSCRIPTION):
        await state.update_data(option="file")
        await state.set_state(UserRoute.file)
        await message.answer(rp.provide_file[lc_])
    else:
        await state.clear()
        await message.answer(rp.file_limit[lc_])


@router.message(UserRoute.videos)
async def video_handler_links(message: Message, state: FSMContext):
    user_state = await state.get_data()
    logger.info("{username}:{id}:video_handler_links:{option}", username=message.from_user.username,
                id=message.from_user.id, option=user_state.get("option"))

    lc_ = await get_lc(message)
    videos: list[YouTubeVideo] = []

    if user_state.get("option") == "channel":
        result, amount, videos = await AppWorker.get_instance().get_channel_videos(message.text)
        if not result:
            await message.answer(rp.channel_not_found[lc_].format(ch_link=message.text))
        elif not amount:
            await message.answer(rp.video_not_found_in_channel[lc_])
        else:
            await message.answer(rp.channel_videos_found[lc_].format(amount=amount,
                                                                     channel_name=videos[0].owner_username))
    elif user_state.get("option") == "video":
        async for result, link, video in AppWorker.get_instance().convert_links_to_videos(message.text):
            if not result:
                await message.answer(text=f"❌ {link}", link_preview_options=LinkPreviewOptions(is_disabled=True))
            else:
                await message.answer(rp.video_found[lc_].format(title=video.title))
                videos.append(video)

    if videos:
        await state.update_data(videos=videos)
        await state.set_state(UserRoute.action)
        await message.answer(rp.choose_action[lc_], reply_markup=action_menu[lc_])
    else:
        await message.answer(rp.video_links_not_found[lc_])
        await state.clear()


@router.message(UserRoute.file)
async def file_receiver(message: Message, state: FSMContext):
    logger.info("{user}:{id}:file_receiver", user=message.from_user.username, id=message.from_user.id)

    lc_ = await get_lc(message)
    await state.clear()

    file = check_content_type(message)
    if not file:
        await message.answer(rp.wrong_file_format[lc_])
        return

    await message.answer(rp.in_progress[lc_])

    status, text_file_path = await AppWorker.get_instance().request_transcription_api(message, file)
    if status:
        await message.answer_document(FSInputFile(text_file_path))
        await AppWorker.get_instance().remove_file(text_file_path)
        logger.info("{user}:{id}:transcription sent", user=message.from_user.username, id=message.from_user.id)
        await decrease_limit(message.from_user.id, AppOperation.TRANSCRIPTION, 1)
    else:
        await message.answer(rp.transcriber_unavailable[lc_])
        logger.warning("{user}:{id}:failed to sent transcription", user=message.from_user.username,
                       id=message.from_user.id)


@router.callback_query(F.data == "download_video", UserRoute.action)
async def video_options_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:video_options_handler")

    lc_ = await get_lc(callback)
    user_state = await state.get_data()

    if "videos" in user_state and len(user_state["videos"]) == 1:
        sent = await callback.message.answer(rp.option_search[lc_])
        options = await AppWorker.get_instance().get_video_options(user_state["videos"][0])
        await sent.delete()
        await callback.message.answer(
            text=rp.available_options[lc_].format(title=user_state["videos"][0].title),
            reply_markup=generate_option_keyboard(options)
        )
        await state.update_data(video_options=options)
        await state.set_state(UserRoute.single_video_options)
    else:
        await callback.message.answer(rp.how_to_choose_option[lc_], reply_markup=option_chooser_menu[lc_])
        await state.set_state(UserRoute.load_options)


@router.callback_query(UserRoute.load_options)
async def download_video_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:download_video")
    lc_ = await get_lc(callback)
    user_state = await state.get_data()
    videos = user_state.get("videos", [])

    if not await validate_limit(callback.from_user.id, AppOperation.VIDEO):
        await callback.bot.send_message(chat_id=callback.from_user.id,
                                        text=rp.video_limit[lc_])
        await state.clear()
        return

    if callback.data == "single_option" and videos:
        sent = await callback.message.answer(rp.option_search[lc_])
        options = await AppWorker.get_instance().get_video_options(videos[0])
        await sent.delete()
        await callback.message.answer(
            rp.available_options[lc_].format(title=videos[0].title), reply_markup=generate_option_keyboard(options)
        )
        await state.update_data(video_options=options)
        await state.set_state(UserRoute.single_video_options)
    elif callback.data == "multi_option" and videos:
        await callback.message.answer(
            rp.option_search_expl[lc_], reply_markup=standard_video_options_menu
        )
        await state.set_state(UserRoute.multi_video_options)
    elif callback.data == "cancel":
        await callback.message.answer(rp.cancel_reply[lc_])
        await state.clear()


@router.callback_query(UserRoute.single_video_options)
async def download_video_with_single_option(callback: CallbackQuery, state: FSMContext):
    logger.info("{username}:{id}:callback:single_video_options", username=callback.from_user.username,
                id=callback.from_user.id)
    lc_ = await get_lc(callback)
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer(rp.in_progress[lc_])
    user_state = await state.get_data()
    async_task = asyncio.create_task(
        AppWorker.get_instance().download_video_worker(
            DownloadTask(
                id=f"{callback.message.chat.id}{callback.message.message_id}",
                video=user_state["videos"].pop(0),
                options=next(filter(lambda x: x.__str__() == callback.data, user_state.get("video_options", []))),
            )
        )
    )

    await task_completion_loop([async_task], callback, lc_)
    await decrease_limit(callback.from_user.id, AppOperation.VIDEO, 1)

    if user_state.get("videos", None):
        await state.update_data(videos=user_state.get("videos"))
        await state.set_state(UserRoute.load_options)
        await callback.message.answer(rp.continue_msg[lc_], reply_markup=proceed_simple_menu[lc_])
    else:
        await callback.message.answer(rp.videos_downloaded[lc_])
        await state.clear()


@router.callback_query(UserRoute.multi_video_options)
async def download_video_with_multi_option(callback: CallbackQuery, state: FSMContext):
    logger.info("{username}:{id}:callback:multi_video_options", username=callback.from_user.username,
                id=callback.from_user.id)
    lc_ = await get_lc(callback)
    await callback.answer("🚀", show_alert=True)
    await callback.message.answer(rp.in_progress[lc_])
    user_state = await state.get_data()
    width, height, fps = map(int, callback.data.split(":"))
    await state.clear()
    await check_privilege_and_load(callback=callback,
                                   language_code=lc_,
                                   worker=AppWorker.get_instance().download_video_worker,
                                   videos=user_state.get("videos", []),
                                   options=VideoOptions(width=width, height=height, fps=fps))


@router.callback_query(F.data == "download_audio", UserRoute.action)
async def download_audio_handler(callback: CallbackQuery, state: FSMContext):
    logger.info("{username}:{id} callback : download_audio", username=callback.from_user.username,
                id=callback.from_user.id)
    lc_ = await get_lc(callback)

    if not await validate_limit(callback.from_user.id, AppOperation.AUDIO):
        await callback.bot.send_message(chat_id=callback.from_user.id,
                                        text=rp.audio_limit[lc_])
        await state.clear()
        return

    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer(rp.in_progress[lc_])
    await check_privilege_and_load(callback=callback,
                                   language_code=lc_,
                                   worker=AppWorker.get_instance().download_audio_worker,
                                   videos=user_state.get("videos", []))


@router.callback_query(F.data == "download_subtitle", UserRoute.action)
async def download_subtitle_handler(callback: CallbackQuery, state: FSMContext):
    logger.info("{username}:{id} callback : download_subtitle", username=callback.from_user.username,
                id=callback.from_user.id)
    lc_ = await get_lc(callback)

    if not await validate_limit(callback.from_user.id, AppOperation.SUBTITLE):
        await callback.bot.send_message(chat_id=callback.from_user.id,
                                        text=rp.subtitle_limit[lc_])
        await state.clear()
        return

    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer(rp.in_progress[lc_])
    await check_privilege_and_load(callback=callback,
                                   language_code=lc_,
                                   worker=AppWorker.get_instance().download_subtitles_worker,
                                   videos=user_state.get("videos", []))


@router.message()
async def any_mes(message: Message):
    logger.info("{username}:{id}:message:{text}", username=message.from_user.username,
                id=message.from_user.id, text=message.text)
    sent = await message.answer("🤔")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()
