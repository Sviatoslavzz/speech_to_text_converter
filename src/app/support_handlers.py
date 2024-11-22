import asyncio
from collections.abc import Callable

from aiogram.types import CallbackQuery, FSInputFile, LinkPreviewOptions
from loguru import logger

from objects import DownloadTask, VideoOptions, YouTubeVideo
from workers import launch_coroutines, launch_one_coroutine, remove_file


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
                logger.info(f"{callback.message.from_user.id}:link to storage sent")
            else:
                await callback.message.answer_document(
                    FSInputFile(
                        path=result_task.local_path,
                        filename=f"{result_task.video.title}{result_task.local_path.suffix}",
                    )
                )
                logger.info(f"{callback.message.from_user.id}:file sent")
                remove_file(result_task.local_path)
        else:
            await callback.message.answer(result_task.message.message["ru"])


async def check_privilege_and_load(callback: CallbackQuery,
                                   worker: Callable,
                                   videos: list[YouTubeVideo],
                                   options: VideoOptions | None = None):
    if callback.from_user.id in [123]:  # allowed user list
        """launch all tasks at a time"""
        coroutines = launch_coroutines(
            async_worker=worker,
            id_=f"{callback.from_user.id}{callback.message.message_id}",
            videos=videos,
            options=options or VideoOptions(),
        )
        await task_completion_loop(coroutines, callback)
    else:
        """one task per user at a time"""
        for coroutine in launch_one_coroutine(
                async_worker=worker,
                id_=f"{callback.from_user.id}{callback.message.message_id}",
                videos=videos,
                options=options or VideoOptions(),
        ):
            await task_completion_loop(coroutine, callback)
