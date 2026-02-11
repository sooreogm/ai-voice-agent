
import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


def setup_logging(level: str):
    """Sets up the logging for the application."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format="{level} {message}",
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
