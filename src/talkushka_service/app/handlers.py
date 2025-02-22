import asyncio

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions, Message
from loguru import logger

from talkushka_service.app import replies as rp
from talkushka_service.app.filters import MainButtonFilter
from talkushka_service.app.keyboards import (
    action_menu,
    approve_menu,
    generate_option_keyboard,
    help_menu,
    main_menu,
    option_chooser_menu,
    proceed_simple_menu,
    standard_video_options_menu,
)
from talkushka_service.app.states import HelpRoute, UserRoute
from talkushka_service.app.support_handlers import (
    check_content_type,
    check_privilege_and_load,
    lc,
    task_completion_loop,
)
from talkushka_service.app_worker import AppWorker
from talkushka_service.objects import (
    DownloadOptions,
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
    await message.answer(rp.welcome_message, reply_markup=main_menu[lc(message)])


@router.message(Command("help"))
async def command_help_handler(message: Message):
    """
    Receives messages with `/help` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/HELP")
    await message.answer(rp.help_reply[lc(message)], reply_markup=help_menu[lc(message)])


@router.callback_query(F.data == "change_language")
async def change_language_handler(callback: CallbackQuery):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:change_language")
    await callback.message.answer(rp.change_language_reply[lc(callback)].format(lc=lc(callback)))
    await callback.message.answer("This feature is in development")  # TODO tmp message


@router.callback_query(F.data == "contact_helpdesk")
async def contact_helpdesk_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:contact_helpdesk")
    await callback.message.answer(rp.contact_helpdesk_reply[lc(callback)])
    await state.set_state(HelpRoute.validation)


@router.message(HelpRoute.validation)
async def helpdesk_validation_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:helpdesk_validation")
    await message.answer(rp.validate_helpdesk_message_reply[lc(message)].format(r=message.text),
                         reply_markup=approve_menu[lc(message)])
    await state.update_data(validation=message.text)
    await state.set_state(HelpRoute.approve)


@router.callback_query(F.data == "approve", HelpRoute.approve)
async def approve_helpdesk_request_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:approve_helpdesk_request")
    await callback.message.answer(rp.helpdesk_sent_reply[lc(callback)])
    state_data = await state.get_data()
    await callback.bot.send_message(384173538,
                                    rp.helpdesk_mess.format(un=callback.from_user.username,
                                                            uid=callback.from_user.id) + \
                                    state_data.get("validation", ""))  # TODO hardcode
    await state.clear()


@router.callback_query(F.data == "cancel", HelpRoute.approve)
async def cancel_helpdesk_request_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:cancel_helpdesk_request")
    await callback.message.answer(rp.cancel_reply[lc(callback)])
    await state.clear()


@router.message(MainButtonFilter(rp.choose_video_button.values()))
async def video_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:video_handler")
    await state.update_data(option="video")
    await state.set_state(UserRoute.videos)
    await message.answer(rp.provide_links)


@router.message(MainButtonFilter(rp.choose_channel_button.values()))
async def channel_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:channel_handler")
    await state.update_data(option="channel")
    await state.set_state(UserRoute.videos)
    await message.answer(rp.provide_channel)


@router.message(MainButtonFilter(rp.choose_file_button.values()))
async def file_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:file_handler")
    await state.update_data(option="file")
    await state.set_state(UserRoute.file)
    await message.answer(rp.provide_file)


@router.message(UserRoute.videos)
async def video_handler_links(message: Message, state: FSMContext):
    user_state = await state.get_data()
    logger.info(f"{message.from_user.username}:{message.from_user.id}:video_handler_links:{user_state.get("option")}")

    videos: list[YouTubeVideo] = []

    if user_state.get("option") == "channel":
        result, amount, videos = await AppWorker.get_instance().get_channel_videos(message.text)
        if not result:
            await message.answer(f"Не нашел канал по данной ссылке {message.text.strip()} ❌")
        elif not amount:
            await message.answer("Не нашел видео на данном канале ❌")
        else:
            await message.answer(f"Нашел {amount} видео на канале {videos[0].owner_username} ✅")
    elif user_state.get("option") == "video":
        async for result, link, video in AppWorker.get_instance().convert_links_to_videos(message.text):
            if not result:
                await message.answer(text=f"{link} ❌", link_preview_options=LinkPreviewOptions(is_disabled=True))
            else:
                await message.answer(f"Нашел видео {video.title} ✅")
                videos.append(video)

    if videos:
        await state.update_data(videos=videos)
        await state.set_state(UserRoute.action)
        await message.answer("Тогда выбирай действие 🏄‍♂️", reply_markup=action_menu)
    else:
        await message.answer("Не нашел корректные ссылки.")
        await state.clear()


@router.message(UserRoute.file)
async def file_receiver(message: Message, state: FSMContext):
    logger.info("{user}:{id}:file_receiver", user=message.from_user.username, id=message.from_user.id)

    await state.clear()

    file = check_content_type(message)
    if not file:
        await message.answer("Упс, кажется такой файл не подойдет ☹️")
        return

    await message.answer("Принято в работу!")

    status, text_file_path = await AppWorker.get_instance().request_transcription_api(message, file)
    if status:
        await message.answer_document(FSInputFile(text_file_path))
        await AppWorker.get_instance().remove_file(text_file_path)
        logger.info("{user}:{id}:transcription sent", user=message.from_user.username, id=message.from_user.id)
    else:
        await message.answer("К сожалению, сервис транскрибации недоступен в данный момент 😓")
        logger.warning("{user}:{id}:failed to sent transcription", user=message.from_user.username,
                       id=message.from_user.id)


@router.callback_query(F.data == "download_video", UserRoute.action)
async def video_options_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:video_options_handler")

    user_state = await state.get_data()
    if "videos" in user_state and len(user_state["videos"]) == 1:
        sent = await callback.message.answer("Ищу доступные опции для видео..")
        options = await AppWorker.get_instance().get_video_options(user_state["videos"][0])
        await sent.delete()
        await callback.message.answer(
            f"Доступные опции для видео {user_state["videos"][0].title}",
            reply_markup=generate_option_keyboard(options)
        )
        await state.update_data(video_options=options)
        await state.set_state(UserRoute.single_video_options)
    else:
        await callback.message.answer("Как предпочитаешь выбирать качество видео?", reply_markup=option_chooser_menu)
        await state.set_state(UserRoute.load_options)


@router.callback_query(UserRoute.load_options)
async def download_video_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:download_video")
    user_state = await state.get_data()
    videos = user_state.get("videos", [])
    if callback.data == "single_option" and videos:
        sent = await callback.message.answer("Ищу доступные опции для видео..")
        options = await AppWorker.get_instance().get_video_options(videos[0])
        await sent.delete()
        await callback.message.answer(
            f"Доступные опции для видео {videos[0].title}", reply_markup=generate_option_keyboard(options)
        )
        await state.update_data(video_options=options)
        await state.set_state(UserRoute.single_video_options)
    elif callback.data == "multi_option" and videos:
        await callback.message.answer(
            "Поиск осуществляется <= выбранной опции", reply_markup=standard_video_options_menu
        )
        await state.set_state(UserRoute.multi_video_options)
    elif callback.data == "cancel":
        await callback.message.answer("Галя, у нас отмена!")
        await state.clear()


@router.callback_query(UserRoute.single_video_options)
async def download_video_with_single_option(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id} callback : single_video_options")
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")
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

    await task_completion_loop([async_task], callback)

    await state.update_data(videos=user_state.get("videos"))
    await state.set_state(UserRoute.load_options)
    if user_state.get("videos", None):
        await callback.message.answer("Продолжаем?", reply_markup=proceed_simple_menu)
    else:
        await callback.message.answer("Мы скачали все видео")
        await state.clear()


@router.callback_query(UserRoute.multi_video_options)
async def download_video_with_multi_option(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:multi_video_options")
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")
    user_state = await state.get_data()
    width, height, fps = map(int, callback.data.split(":"))
    await state.clear()
    await check_privilege_and_load(callback=callback,
                                   worker=AppWorker.get_instance().download_video_worker,
                                   videos=user_state.get("videos", []),
                                   options=VideoOptions(width=width, height=height, fps=fps))


@router.callback_query(F.data == "download_audio", UserRoute.action)
async def download_audio_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id} callback : download_audio")
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")
    await check_privilege_and_load(callback=callback,
                                   worker=AppWorker.get_instance().download_audio_worker,
                                   videos=user_state.get("videos", []))


@router.callback_query(F.data == "download_text", UserRoute.action)
async def download_text_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id} callback : download_text")
    await state.update_data(action=DownloadOptions.TEXT)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")
    await check_privilege_and_load(callback=callback,
                                   worker=AppWorker.get_instance().download_subtitles_worker,
                                   videos=user_state.get("videos", []))


@router.message()
async def any_mes(message: Message):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:message:{message.text}")
    sent = await message.answer("🤔")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()
