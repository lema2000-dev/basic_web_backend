import logging

from basic_web_backend.logging_config import create_logger

def test_create_logger_writes_messages_to_file(tmp_path):
    log_file = tmp_path / "backend.log"
    logger = create_logger(name="test.file.logger", log_file=log_file, log_level="INFO")

    logger.info("Application started")

    for handler in logger.handlers:
        handler.flush()

    log_content = log_file.read_text(encoding="utf-8")

    assert "INFO" in log_content
    assert "Application started" in log_content

def test_create_logger_creates_parent_directory(tmp_path):
    log_file = tmp_path / "logs" / "backend.log"
    create_logger(name="test.directory.logger", log_file=log_file)

    assert log_file.parent.is_dir()
    assert log_file.is_file()

def test_create_logger_can_disable_file_logging():
    logger = create_logger(name="test.disabled.file.logger", log_file=None)

    assert not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)

def test_create_logger_uses_rotating_file_handler(tmp_path):
    from logging.handlers import RotatingFileHandler

    log_file = tmp_path / "backend.log"
    logger = create_logger(
        name="test.rotating.logger",
        log_file=log_file,
        log_max_bytes=1024,
        log_backup_count=3
    )

    file_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]

    assert len(file_handlers) == 1

    handler = file_handlers[0]

    assert handler.maxBytes == 1024
    assert handler.backupCount == 3