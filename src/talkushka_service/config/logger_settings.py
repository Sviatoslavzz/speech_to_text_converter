from sys import stdout

from loguru import logger

from talkushka_service.config.settings import settings

logger.remove(0)

logger.add(
    sink=stdout,
    level=settings.LOG_LEVEL,
    backtrace=True,
    diagnose=True,
    enqueue=True,
)
