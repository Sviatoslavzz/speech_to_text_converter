import asyncio
from collections.abc import Callable

from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions
from loguru import logger

from talkushka_service.app.db_operation import (
    decrease_audio_limit,
    decrease_subtitle_limit,
    decrease_video_limit,
    validate_audio_download_limit,
    validate_subtitle_download_limit,
    validate_video_download_limit,
)
from talkushka_service.app.replies import audio_limit, external_storage_ms, subtitle_limit, video_limit
from talkushka_service.app_worker import AppWorker
from talkushka_service.model.objects import DownloadTask, VideoOptions, YouTubeVideo


async def task_completion_loop(coroutines: list[asyncio.Task], callback: CallbackQuery, language_code: str):
    for complete_task in asyncio.as_completed(coroutines):
        result_task: DownloadTask = await complete_task
        await asyncio.sleep(0.5)
        if result_task.result:
            if result_task.storage_link:
                await callback.message.answer(
                    external_storage_ms[language_code].format(title=result_task.video.title,
                                                              link=result_task.storage_link,
                                                              message=result_task.message[language_code]),
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
                logger.info("{uname}:{id}:link to storage sent", uname=callback.message.from_user.username,
                            id=callback.message.from_user.id)
            else:
                await callback.message.answer_document(
                    FSInputFile(
                        path=result_task.local_path,
                        filename=f"{result_task.video.title}{result_task.local_path.suffix}",
                    )
                )
                logger.info("{uname}:{id}:file sent", uname=callback.message.from_user.username,
                            id=callback.message.from_user.id)
                await AppWorker.get_instance().remove_file(result_task.local_path)
        else:
            await callback.message.answer(result_task.message["ru"])


async def check_privilege_and_load(callback: CallbackQuery,
                                   language_code: str,
                                   worker: Callable,
                                   videos: list[YouTubeVideo],
                                   options: VideoOptions | None = None):
    """
    Privilege means user can download asynchronously all tasks.
    """
    if callback.from_user.id in [123]:  # allowed user list
        """launch all tasks at a time"""
        coroutines = AppWorker.get_instance().launch_coroutines(
            async_worker=worker,
            id_=f"{callback.from_user.id}:{callback.message.message_id}",
            videos=videos,
            options=options or VideoOptions(),
        )
        await task_completion_loop(coroutines, callback, language_code)
    else:
        """one task per user at a time"""
        async for coroutine in AppWorker.get_instance().launch_one_coroutine(
                async_worker=worker,
                id_=f"{callback.from_user.id}:{callback.message.message_id}",
                videos=videos,
                options=options or VideoOptions(),
        ):
            await task_completion_loop(coroutine, callback, language_code)
            if not await decrease_and_validate_limits(callback, language_code, worker.__name__):
                break


async def decrease_and_validate_limits(callback: CallbackQuery, language_code: str, worker_name: str):
    if worker_name == "download_video_worker":
        await decrease_video_limit(callback)
        if not await validate_video_download_limit(callback):
            await callback.bot.send_message(chat_id=callback.from_user.id,
                                            text=video_limit[language_code])
            return False
    elif worker_name == "download_audio_worker":
        await decrease_audio_limit(callback)
        if not await validate_audio_download_limit(callback):
            await callback.bot.send_message(chat_id=callback.from_user.id,
                                            text=audio_limit[language_code])
            return False
    elif worker_name == "download_subtitles_worker":
        await decrease_subtitle_limit(callback)
        if not await validate_subtitle_download_limit(callback):
            await callback.bot.send_message(chat_id=callback.from_user.id,
                                            text=subtitle_limit[language_code])
            return False

    return True


def check_content_type(message):
    """
    Checks the content type of the message.
    :return: file_info or None
    """
    if message.content_type == "audio":
        return message.audio
    if message.content_type == "video":
        return message.video
    if message.content_type == "document":
        return message.document
    logger.warning("{username}:{user_id}:invalid file type:{type}",
                   username=message.from_user.username,
                   user_id=message.from_user.id,
                   type=message.content_type)
    return None
