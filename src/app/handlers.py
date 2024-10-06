import asyncio
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from google.api_core.exceptions import BadRequest
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
from objects import DownloadOptions, UserRoute, YouTubeVideo
from transcribers.abscract import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber
from transcribers.worker import TranscriberWorker
from app.main_workers import download_video_worker, download_audio_worker, download_subtitles_worker, \
    convert_links_to_videos, get_channel_videos_worker

# TODO добавление через config
WHISPER_MODEL = "small"
SAVING_FOLDER = "saved_files"
TRANSCRIBER: type[AbstractTranscriber] = FasterWhisperTranscriber

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
    await message.answer("За помощью лучше обращаться к chat GPT 🤷‍♂️")


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
        result, amount, videos = await get_channel_videos_worker(message.text)
        if not result:
            await message.answer(f"Не нашел канал по данной ссылке{message.text.strip()} ❌")
        elif not amount:
            await message.answer(f"Не нашел видео на данном канале ❌")
        else:
            await message.answer(f"Нашел {amount} видео на канале ✅")
    elif user_state.get("option") == "video":
        async for result, link, video in convert_links_to_videos(message.text):
            if not result:
                await message.answer(f"{link} ❌")
            else:
                await message.answer(f"{video.id} ✅")
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
        logger.warning(f"{message.from_user.username}:{message.chat.id} Received invalid file type: {message.content_type}")
        await message.answer("Упс, кажется такой файл не подойдет ☹️")
        return

    logger.info(f"{message.from_user.username}:{message.chat.id} Received file for transcribing")
    await message.answer("Принято в работу!")

    try:
        file_info = await message.bot.get_file(file.file_id)
        save_path = f"./{SAVING_FOLDER}/{file.file_name}"
        await message.bot.download_file(file_info.file_path, destination=save_path)
        logger.info(
            f"{message.from_user.username}:{message.chat.id} File loaded from tg and saved to\n{save_path}")

        worker = TranscriberWorker()  # TODO убрать отсюда
        result, path_ = await worker.transcribe(Path(save_path))
        if result:
            await message.answer_document(FSInputFile(Path(path_)))
            logger.info(f"{message.chat.id} Text file sent")
            path_.unlink(missing_ok=True)
        else:
            await message.answer("К сожалению, что-то пошло не так и я не смог сделать транскрипцию 😓")
    except BadRequest:
        logger.error(f"{message.from_user.username}:{message.chat.id} Failed to load file from tg")


@router.callback_query(F.data == "download_video", UserRoute.option)
async def download_video_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.message.chat.id} Received callback, download_video")
    await state.update_data(action=DownloadOptions.VIDEO)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")

    async for result, path_ in download_video_worker(user_state.get("videos"), str(callback.message.chat.id)):
        if result:
            await callback.message.answer_document(FSInputFile(Path(path_)))
            logger.info(f"{callback.message.chat.id} Video file sent")
            path_.unlink(missing_ok=True)
        else:
            await callback.message.answer(f"Не смог скачать видео по ссылке: {path_}")


@router.callback_query(F.data == "download_audio", UserRoute.option)
async def download_audio_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.message.chat.id} Received callback, download_audio")
    await state.update_data(action=DownloadOptions.AUDIO)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")

    async for result, path_ in download_audio_worker(user_state.get("videos"), str(callback.message.chat.id)):
        if result:
            await callback.message.answer_document(FSInputFile(Path(path_)))
            logger.info(f"{callback.message.chat.id} Audio file sent")
            path_.unlink(missing_ok=True)
        else:
            await callback.message.answer(f"Не смог скачать аудио по ссылке: {path_}")


@router.callback_query(F.data == "download_text", UserRoute.option)
async def download_text_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"{callback.from_user.username}:{callback.message.chat.id} Received callback, download_text")
    await state.update_data(action=DownloadOptions.TEXT)
    user_state = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")

    async for result, path_ in download_subtitles_worker(user_state.get("videos"), str(callback.message.chat.id)):
        if result:
            await callback.message.answer_document(FSInputFile(Path(path_)))
            logger.info(f"{callback.message.chat.id} Text file sent")
            path_.unlink(missing_ok=True)
        else:
            await callback.message.answer(f"Не смог скачать субтитры по ссылке: {path_}")


@router.message()
async def any_mes(message: Message):
    logger.info(f"{message.from_user.username}:{message.chat.id} Received any message\n{message.text}")
    sent = await message.answer("🤔")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()
