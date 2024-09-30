import asyncio
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from google.api_core.exceptions import BadRequest
from humanfriendly.terminal import message
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
from objects import DownloadOptions, UserRoute
from transcribers.abscract import AbstractTranscriber
from transcribers.faster_whisper_transcriber import FasterWhisperTranscriber
from transcribers.worker import TranscriberWorker
from app.main_workers import download_video_worker

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
    logger.info(f"Got a start command from chat {message.chat.id}")
    await message.answer(welcome_message, reply_markup=main_menu)


@router.message(Command("help"))
async def command_help_handler(message: Message):
    """
    Receives messages with `/help` command
    """
    logger.info(f"Got a help command from chat {message.chat.id}")
    await message.answer("За помощью лучше обращаться к chat GPT 🤷‍♂️")


@router.message(F.text == choose_video_button)
async def video_handler(message: Message, state: FSMContext):
    logger.info(f"Received message, id {message.message_id}, chat: {message.chat.id}:\n{message.text}")
    await state.update_data(option="video")
    await state.set_state(UserRoute.links)
    await message.answer(provide_links)


@router.message(F.text == choose_channel_button)
async def channel_handler(message: Message, state: FSMContext):
    logger.info(f"Received message, id {message.message_id}, chat: {message.chat.id}:\n{message.text}")
    await state.update_data(option="channel")
    await state.set_state(UserRoute.links)
    await message.answer(provide_channel)


@router.message(F.text == choose_file_button)
async def file_handler(message: Message, state: FSMContext):
    logger.info(f"Received message, id {message.message_id}, chat: {message.chat.id}:\n{message.text}")
    await state.update_data(option="file")
    await state.set_state(UserRoute.file)
    await message.answer(provide_file)


@router.message(UserRoute.links)
async def video_handler_links(message: Message, state: FSMContext):
    logger.info(f"Received links, id {message.message_id}, chat: {message.chat.id}")
    await state.update_data(links=message.text)
    await state.set_state(UserRoute.option)
    await message.answer("Тогда выбирай действие 🏄‍♂️", reply_markup=options_menu)


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
        logger.warning(f"Received invalid file type: {message.content_type}")
        await message.answer("Упс, кажется такой файл не подойдет ☹️")
        return

    logger.info(f"Received file, id {message.message_id}, chat: {message.chat.id}")
    await message.answer("Принято в работу!")

    try:
        file_info = await message.bot.get_file(file.file_id)
        await message.bot.download_file(file_info.file_path, destination=f"./{SAVING_FOLDER}/{file.file_name}")
        logger.info(f"File loaded from tg and saved {f"./{SAVING_FOLDER}/{file.file_name}"}, chat: {message.chat.id}")

        worker = TranscriberWorker()  # TODO убрать отсюда
        result, path_ = await worker.transcribe(Path(f"./{SAVING_FOLDER}/{file.file_name}"))
        if result:
            await message.answer_document(FSInputFile(Path(path_)))
            logger.info(f"File sent to user {message.chat.id}")
        else:
            await message.answer("К сожалению, что-то пошло не так и я не смог сделать транскрипцию 😓")
    except BadRequest:
        logger.error(f"Failed to process a file, id {message.message_id}, chat: {message.chat.id}")


@router.callback_query(F.data == "download_video")
async def download_video_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Received callback, download_video, chat: {callback.message.chat.id}")
    await state.update_data(action=DownloadOptions.VIDEO)
    options = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer("Принято в работу!")

    async for result, path_ in download_video_worker(options):
        if result:
            await callback.message.answer_video(FSInputFile(Path(path_)))
            path_.unlink(missing_ok=True)
        else:
            await callback.message.answer(f"Не смог скачать видео по ссылке: {path_}")


@router.callback_query(F.data == "download_audio")
async def download_audio_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Received callback, download_audio, chat: {callback.message.chat.id}")
    await state.update_data(action=DownloadOptions.AUDIO)
    options = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer(f"твои опции: {options}")


@router.callback_query(F.data == "download_text")
async def download_text_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Received callback, download_text, chat: {callback.message.chat.id}")
    await state.update_data(action=DownloadOptions.TEXT)
    options = await state.get_data()
    await state.clear()
    await callback.answer("🚀", show_alert=False)
    await callback.message.answer(f"твои опции: {options}")


@router.message()
async def any_mes(message: Message):
    logger.info(f"Received message, id {message.message_id}, chat: {message.chat.id}:\n{message.text}")
    sent = await message.answer("🤔")
    await asyncio.sleep(5)
    await message.delete()
    await sent.delete()
