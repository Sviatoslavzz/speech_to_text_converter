import asyncio
from collections.abc import Callable

from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions, Message
from loguru import logger

from talkushka_service.app_worker import AppWorker
from talkushka_service.model.objects import DownloadTask, VideoOptions, YouTubeVideo


async def task_completion_loop(coroutines: list[asyncio.Task], callback: CallbackQuery):
    for complete_task in asyncio.as_completed(coroutines):
        result_task: DownloadTask = await complete_task
        await asyncio.sleep(0.5)
        if result_task.result:
            if result_task.storage_link:
                await callback.message.answer(
                    f"💥 Видео: {result_task.video.title}\n"
                    f"Прикрепляю ссылку на внешнее хранилище, {result_task.message["ru"]}\n"
                    f"{result_task.storage_link}",
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
                                   worker: Callable,
                                   videos: list[YouTubeVideo],
                                   options: VideoOptions | None = None):
    if callback.from_user.id in [123]:  # allowed user list
        """launch all tasks at a time"""
        coroutines = AppWorker.get_instance().launch_coroutines(
            async_worker=worker,
            id_=f"{callback.from_user.id}:{callback.message.message_id}",
            videos=videos,
            options=options or VideoOptions(),
        )
        await task_completion_loop(coroutines, callback)
    else:
        """one task per user at a time"""
        async for coroutine in AppWorker.get_instance().launch_one_coroutine(
                async_worker=worker,
                id_=f"{callback.from_user.id}:{callback.message.message_id}",
                videos=videos,
                options=options or VideoOptions(),
        ):
            await task_completion_loop(coroutine, callback)


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


def lc(msg: CallbackQuery | Message):
    """
    Get the language code of the user chat.
    """
    return "ru" if msg.from_user.language_code == "ru" else "en"
