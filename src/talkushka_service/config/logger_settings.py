from sys import stdout

from loguru import logger

logger.remove(0)

logger.add(
    sink=stdout,
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    enqueue=True,
)
