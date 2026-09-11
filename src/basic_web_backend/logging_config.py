import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}

DEFAULT_LOG_FORMAT = (
    "%(asctime)s "
    "%(levelname)s "
    "%(name)s "
    "%(message)s"
)

def create_logger(
    name="basic_web_backend",
    log_file=None,
    log_level="INFO",
    log_max_bytes=1_000_000,
    log_backup_count=5
):
    logger = logging.getLogger(name)

    level = LOG_LEVELS.get(str(log_level).upper())

    if level is None:
        raise ValueError(f"Invalid log level: {log_level!r}")

    logger.setLevel(level)
    logger.propagate = False

    _remove_existing_handlers(logger)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count,
            encoding="utf-8"
        )

        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        logger.addHandler(handler)

    return logger

def _remove_existing_handlers(logger):
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    