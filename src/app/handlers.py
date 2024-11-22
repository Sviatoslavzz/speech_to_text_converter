import asyncio
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions, Message
from loguru import logger

from app.keyboards import (
    action_menu,
    generate_option_keyboard,
    main_menu,
    option_chooser_menu,
    proceed_simple_menu,
    standard_video_options_menu,
)
from app.replies import (
    choose_channel_button,
    choose_file_button,
    choose_video_button,
    provide_channel,
    provide_file,
    provide_links,
    welcome_message,
)
from app.support_handlers import check_privilege_and_load, task_completion_loop
from objects import (
    SERVER,
    DownloadOptions,
    DownloadTask,
    TranscriptionTask,
    UserRoute,
    VideoOptions,
    YouTubeVideo,
    get_save_dir,
)
from workers import (
    convert_links_to_videos,
    download_audio_worker,
    download_subtitles_worker,
    download_video_worker,
    get_channel_videos,
    get_video_options,
    remove_file,
    run_transcriber_executor,
)

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    """
    Receives messages with `/start` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/START")
    await message.answer(welcome_message, reply_markup=main_menu)


@router.message(Command("help"))
async def command_help_handler(message: Message):
    """
    Receives messages with `/help` command
    """
    logger.info(f"{message.from_user.username}:{message.from_user.id}:/HELP")
    sent = await message.answer("За помощью лучше обращаться к chat GPT 🤷‍♂️")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()


@router.message(F.text == choose_video_button)
async def video_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:video_handler")
    await state.update_data(option="video")
    await state.set_state(UserRoute.videos)
    await message.answer(provide_links)


@router.message(F.text == choose_channel_button)
async def channel_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:channel_handler")
    await state.update_data(option="channel")
    await state.set_state(UserRoute.videos)
    await message.answer(provide_channel)


@router.message(F.text == choose_file_button)
async def file_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:router:file_handler")
    await state.update_data(option="file")
    await state.set_state(UserRoute.file)
    await message.answer(provide_file)


@router.message(UserRoute.videos)
async def video_handler_links(message: Message, state: FSMContext):
    user_state = await state.get_data()
    logger.info(f"{message.from_user.username}:{message.from_user.id}:video_handler_links:{user_state.get("option")}")

    videos: list[YouTubeVideo] = []

    if user_state.get("option") == "channel":
        result, amount, videos = await get_channel_videos(message.text)
        if not result:
            await message.answer(f"Не нашел канал по данной ссылке {message.text.strip()} ❌")
        elif not amount:
            await message.answer("Не нашел видео на данном канале ❌")
        else:
            await message.answer(f"Нашел {amount} видео на канале {videos[0].owner_username} ✅")
    elif user_state.get("option") == "video":
        async for result, link, video in convert_links_to_videos(message.text):
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
    logger.info(f"{message.from_user.username}:{message.from_user.id}:file_receiver")

    await state.clear()

    if message.content_type == "audio":
        file = message.audio
    elif message.content_type == "video":
        file = message.video
    elif message.content_type == "document":
        file = message.document
    else:
        logger.warning(f"{message.from_user.username}:{message.from_user.id}:invalid file type:{message.content_type}")
        await message.answer("Упс, кажется такой файл не подойдет ☹️")
        return

    await message.answer("Принято в работу!")
    try:
        file_info = await message.bot.get_file(file.file_id)  # если локально - то ждет полной загрузки
        if SERVER == "telegram":
            task = TranscriptionTask(
                origin_path=get_save_dir() / f"{message.message_id!s}_{file.file_name}",
                id=f"{message.from_user.id}{message.message_id}"
            )
            await message.bot.download_file(file_info.file_path, destination=task.origin_path)
        elif SERVER == "local":
            task = TranscriptionTask(
                origin_path=Path(file_info.file_path),
                id=f"{message.from_user.id}{message.message_id}",
            )
        else:
            raise ValueError("SERVER must be 'telegram' or 'local'")

        result_tasks = await run_transcriber_executor([task])

        for r_task in result_tasks:
            if r_task.result:
                await message.answer_document(FSInputFile(r_task.local_path))
                logger.info(f"{message.from_user.id}:file sent")
                remove_file(r_task.origin_path)
                remove_file(r_task.local_path)
            else:
                await message.answer("К сожалению, что-то пошло не так и я не смог сделать транскрибацию 😓")
    except Exception as e:
        logger.error(f"{message.from_user.username}:{message.from_user.id}:{file.file_id}:{e.__repr__()}")
        await message.answer("Упс, что-то пошло не так!")


@router.callback_query(F.data == "download_video", UserRoute.action)
async def video_options_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:video_options_handler")
    await callback.message.answer("Как предпочитаешь выбирать качество видео?", reply_markup=option_chooser_menu)
    await state.set_state(UserRoute.load_options)


@router.callback_query(UserRoute.load_options)
async def download_video_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id}:callback:download_video")
    user_state = await state.get_data()
    videos = user_state.get("videos", [])
    if callback.data == "single_option" and videos:
        options = await get_video_options(videos[0])
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
        download_video_worker(
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
    await check_privilege_and_load(callback, download_video_worker, user_state.get("videos", []),
                                   VideoOptions(width=width, height=height, fps=fps))


@router.callback_query(F.data == "download_audio", UserRoute.action)
async def download_audio_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id} callback : download_audio")
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")
    await check_privilege_and_load(callback, download_audio_worker, user_state.get("videos", []))


@router.callback_query(F.data == "download_text", UserRoute.action)
async def download_text_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.from_user.id} callback : download_text")
    await state.update_data(action=DownloadOptions.TEXT)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")
    await check_privilege_and_load(callback, download_subtitles_worker, user_state.get("videos", []))


@router.message()
async def any_mes(message: Message):
    logger.info(f"{message.from_user.username}:{message.from_user.id}:message:{message.text}")
    sent = await message.answer("🤔")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()
