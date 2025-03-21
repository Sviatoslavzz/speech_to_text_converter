import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions, Message
from loguru import logger

from talkushka_service.app import replies as rp
from talkushka_service.app.app_worker import AppWorker
from talkushka_service.app.db_operation import (
    decrease_limit,
    get_lc,
    validate_limit,
)
from talkushka_service.app.filters import MainButtonFilter
from talkushka_service.app.keyboards import (
    action_menu,
    generate_option_keyboard,
    option_chooser_menu,
    proceed_simple_menu,
    standard_video_options_menu,
)
from talkushka_service.app.states import UserRoute
from talkushka_service.app.support_handlers import (
    check_content_type,
    check_privilege_and_load,
    task_completion_loop,
)
from talkushka_service.model.objects import (
    AppOperation,
    DownloadTask,
    VideoOptions,
    YouTubeVideo,
)

app_router = Router()

@app_router.message(Command("get_transcription"))
async def command_get_transcription_handler(message: Message):
    raise NotImplementedError


@app_router.message(MainButtonFilter(rp.choose_video_button.values()))
async def video_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:video_handler")
    lc_ = await get_lc(message)
    await state.update_data(option="video")
    await state.set_state(UserRoute.videos)
    await message.answer(rp.provide_links[lc_])


@app_router.message(MainButtonFilter(rp.choose_channel_button.values()))
async def channel_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:channel_handler")
    lc_ = await get_lc(message)
    await state.update_data(option="channel")
    await state.set_state(UserRoute.videos)
    await message.answer(rp.provide_channel[lc_])


@app_router.message(MainButtonFilter(rp.choose_file_button.values()))
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


@app_router.message(UserRoute.videos)
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


@app_router.message(UserRoute.file)
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


@app_router.callback_query(F.data == "download_video", UserRoute.action)
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


@app_router.callback_query(UserRoute.load_options)
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


@app_router.callback_query(UserRoute.single_video_options)
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


@app_router.callback_query(UserRoute.multi_video_options)
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


@app_router.callback_query(F.data == "download_audio", UserRoute.action)
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


@app_router.callback_query(F.data == "download_subtitle", UserRoute.action)
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


@app_router.message()
async def any_mes(message: Message):
    logger.info("{username}:{id}:message:{text}", username=message.from_user.username,
                id=message.from_user.id, text=message.text)
    sent = await message.answer("🤔")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()
