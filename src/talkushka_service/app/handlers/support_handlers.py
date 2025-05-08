import asyncio
from collections.abc import Callable

from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions
from loguru import logger

from talkushka_service.app.app_worker import AppWorker
from talkushka_service.app.db_operation import decrease_limit, validate_limit
from talkushka_service.app.replies import external_storage_ms, get_limit_reply
from talkushka_service.model.objects import DownloadTask, VideoOptions, YouTubeVideo
from talkushka_service.utils.functions import get_app_operation


async def task_completion_loop(coroutines: list[asyncio.Task], callback: CallbackQuery, language_code: str):
    for complete_task in asyncio.as_completed(coroutines):
        await finalize_task(complete_task, callback, language_code)
        await asyncio.sleep(0.5)


async def finalize_task(download_task: asyncio.Task, callback: CallbackQuery, language_code: str):
    """
    Collects the result of DownloadTask.
    Sends appropriate message to user.
    Decreases limit for specific parameter - parameter depends on worker.
    :param download_task: DownloadTask
    :param callback: Callback
    :param language_code: language code
    """
    result_task: DownloadTask = await download_task
    if result_task.result:
        # TODO decrease limit
        # TODO take current worker from task
        asyncio.create_task(
            decrease_limit(callback.from_user.id, get_app_operation(download_task.get_coro().__name__), 1)
        )
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
    if callback.from_user.id in [3841735380, ]:  # allowed user list
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
            await finalize_task(coroutine, callback, language_code)
            if not validate_limit_by_operation(callback, language_code, worker.__name__):
                break


async def validate_limit_by_operation(callback: CallbackQuery, language_code: str, worker_name: str):
    """
    Validates limit by app operation.
    Sends message to user in case limit is reached.
    :param callback: Callback
    :param language_code: language code
    :param worker_name: worker name
    """
    parameter = get_app_operation(worker_name)  # TODO transfer to upper level
    if not await validate_limit(callback.from_user.id, parameter):
        await callback.bot.send_message(chat_id=callback.from_user.id,
                                        text=get_limit_reply(parameter, language_code))
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
    # elif mess

    logger.warning("{username}:{user_id}:invalid file type:{type}",
                   username=message.from_user.username,
                   user_id=message.from_user.id,
                   type=message.content_type)
    return None
