from sys import stdout

from loguru import logger

from talkushka_service.config.settings import settings
from talkushka_service.utils.functions import get_project_root

logger.remove()

if settings.LOG_STREAM_HANDLER:
    logger.add(
        stdout,
        enqueue=True,
        level=settings.LOG_LEVEL,
        backtrace=True,
        diagnose=settings.LOG_LEVEL == "DEBUG",
    )

if settings.LOG_FILE_HANDLER:
    log_dir = get_project_root() / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{settings.TITLE}.log"

    logger.add(
        log_path,
        rotation="00:00",
        retention=3,
        enqueue=True,
        level=settings.LOG_LEVEL,
        backtrace=True,
        diagnose=settings.LOG_LEVEL == "DEBUG",
        serialize=True,
    )
