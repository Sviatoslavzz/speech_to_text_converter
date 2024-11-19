import asyncio
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions, Message
from loguru import logger

from app.keyboards import main_menu, options_menu
from app.replies import (
    choose_channel_button,
    choose_file_button,
    choose_video_button,
    provide_channel,
    provide_file,
    provide_links,
    welcome_message,
)
from objects import AppMessage, DownloadOptions, DownloadTask, TranscriptionTask, UserRoute, YouTubeVideo, get_save_dir
from workers import (
    convert_links_to_videos,
    download_audio_worker,
    download_subtitles_worker,
    download_video_worker,
    get_channel_videos,
    launch_coroutines,
    run_transcriber_executor,
)

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message):
    """
    Receives messages with `/start` command
    """
    logger.info(f"{message.from_user.username}:{message.chat.id} Got a /START command")
    await message.answer(welcome_message, reply_markup=main_menu)


@router.message(Command("help"))
async def command_help_handler(message: Message):
    """
    Receives messages with `/help` command
    """
    logger.info(f"{message.from_user.username}:{message.chat.id} Got a /HELP command")
    sent = await message.answer("За помощью лучше обращаться к chat GPT 🤷‍♂️")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()


@router.message(F.text == choose_video_button)
async def video_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.chat.id} Received message\n{message.text}")
    await state.update_data(option="video")
    await state.set_state(UserRoute.videos)
    await message.answer(provide_links)


@router.message(F.text == choose_channel_button)
async def channel_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.chat.id} Received message\n{message.text}")
    await state.update_data(option="channel")
    await state.set_state(UserRoute.videos)
    await message.answer(provide_channel)


@router.message(F.text == choose_file_button)
async def file_handler(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.chat.id} Received message\n{message.text}")
    await state.update_data(option="file")
    await state.set_state(UserRoute.file)
    await message.answer(provide_file)


@router.message(UserRoute.videos)
async def video_handler_links(message: Message, state: FSMContext):
    logger.info(f"{message.from_user.username}:{message.chat.id} Received links")

    user_state = await state.get_data()
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
        await state.set_state(UserRoute.option)
        await message.answer("Тогда выбирай действие 🏄‍♂️", reply_markup=options_menu)
    else:
        await message.answer("Попробуем еще раз?")
        await state.set_state(UserRoute.videos)


@router.message(UserRoute.file)
async def file_receiver(message: Message, state: FSMContext):
    await state.clear()

    if message.content_type == "audio":
        file = message.audio
    elif message.content_type == "video":
        file = message.video
    elif message.content_type == "document":
        file = message.document
    else:
        logger.warning(
            f"{message.from_user.username}:{message.chat.id} Received invalid file type: {message.content_type}"
        )
        await message.answer("Упс, кажется такой файл не подойдет ☹️")
        return

    logger.info(f"{message.from_user.username}:{message.chat.id} Received file for transcribing")
    await message.answer("Принято в работу!")

    try:
        file_info = await message.bot.get_file(file.file_id) # если локально - то ждет полной загрузки
        # TODO сейчас настроил только для локального сервера - подумать как можно динамически подстраиваться
        # task = TranscriptionTask(
        #     origin_path=get_save_dir() / file.file_name,
        #     id=f"{message.chat.id}{message.message_id}"
        # )
        # await message.bot.download_file(file_info.file_path, destination=task.origin_path)
        task = TranscriptionTask(
            origin_path=Path(file_info.file_path),
            id=f"{message.chat.id}{message.message_id}",
        )

        result_tasks = await run_transcriber_executor([task])

        for r_task in result_tasks:
            if r_task.result:
                await message.answer_document(FSInputFile(r_task.local_path))
                logger.info(f"{message.chat.id} Text file sent")
                r_task.origin_path.unlink(missing_ok=True)
                r_task.local_path.unlink(missing_ok=True)
            else:
                await message.answer("К сожалению, что-то пошло не так и я не смог сделать транскрибацию 😓")
    except Exception as e:
        logger.error(f"{message.from_user.username}:{message.chat.id} Failed to load file from server {e.__repr__()}")
        await message.answer("Упс, что-то пошло не так!")


async def task_completion_loop(coroutines: list, callback: CallbackQuery):
    for complete_task in asyncio.as_completed(coroutines):
        result_task: DownloadTask = await complete_task
        await asyncio.sleep(0.5)
        if result_task.result:
            if result_task.storage_link:
                await callback.message.answer(
                    f"""💥 Видео: {result_task.video.title}
Прикрепляю ссылку на внешнее хранилище, действует 5 минут\n{result_task.storage_link}""",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
                logger.info(f"{callback.message.chat.id} Link to file sent")
            else:
                await callback.message.answer_document(
                    FSInputFile(
                        path=Path(result_task.local_path),
                        filename=f"{result_task.video.title}{result_task.local_path.suffix}",
                    )
                )
                logger.info(f"{callback.message.chat.id} file sent")
                result_task.local_path.unlink(missing_ok=True)
        else:
            await callback.message.answer(result_task.message.message["ru"])


@router.callback_query(F.data == "download_video", UserRoute.option)
async def download_video_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.message.chat.id} Received callback, download_video")
    await state.update_data(action=DownloadOptions.VIDEO)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")

    coroutines = launch_coroutines(
        async_worker=download_video_worker,
        id_=f"{callback.message.chat.id}{callback.message.message_id}",
        videos=user_state.get("videos", []),
    )

    await task_completion_loop(coroutines, callback)


@router.callback_query(F.data == "download_audio", UserRoute.option)
async def download_audio_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.message.chat.id} Received callback, download_audio")
    await state.update_data(action=DownloadOptions.AUDIO)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")

    coroutines = launch_coroutines(
        async_worker=download_audio_worker,
        id_=f"{callback.message.chat.id}{callback.message.message_id}",
        videos=user_state.get("videos", []),
    )

    await task_completion_loop(coroutines, callback)


@router.callback_query(F.data == "download_text", UserRoute.option)
async def download_text_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.message.chat.id} Received callback, download_text")
    await state.update_data(action=DownloadOptions.TEXT)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")

    coroutines = launch_coroutines(
        async_worker=download_subtitles_worker,
        id_=f"{callback.message.chat.id}{callback.message.message_id}",
        videos=user_state.get("videos", []),
    )

    await task_completion_loop(coroutines, callback)


@router.message()
async def any_mes(message: Message):
    logger.info(f"{message.from_user.username}:{message.chat.id} Received any message\n{message.text}")
    sent = await message.answer("🤔")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()
