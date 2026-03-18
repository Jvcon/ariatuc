"""Unified logging configuration for ariatuc.

This module provides centralized logging configuration with:
- File logging with rotation
- Console logging (optional)
- Environment variable configuration
- Structured log format
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Default configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/ariatuc.log"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file rotation settings
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 7  # Keep 7 backup files


def get_log_level() -> int:
    """Get log level from environment or use default.

    Returns:
        logging level constant (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level_name = os.getenv("ARIATUC_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_name, logging.INFO)


def get_log_file() -> Path:
    """Get log file path from environment or use default.

    Returns:
        Path to log file
    """
    log_file = os.getenv("ARIATUC_LOG_FILE", DEFAULT_LOG_FILE)
    return Path(log_file)


def get_console_output() -> bool:
    """Get console output setting from environment.

    Returns:
        True if console output is enabled, False otherwise
    """
    console_env = os.getenv("ARIATUC_LOG_CONSOLE", "false").lower()
    return console_env in ("true", "1", "yes", "on")


def setup_logging(
    log_level: int | None = None,
    log_file: Path | None = None,
    console_output: bool | None = None,
) -> None:
    """Configure application-wide logging.

    Args:
        log_level: Logging level (defaults to environment or INFO)
        log_file: Path to log file (defaults to environment or logs/ariatuc.log)
        console_output: Whether to also output logs to console (defaults to environment or False)
                       Set ARIATUC_LOG_CONSOLE=true to enable console output
    """
    # Determine log level, file, and console output
    if log_level is None:
        log_level = get_log_level()
    if log_file is None:
        log_file = get_log_file()
    if console_output is None:
        console_output = get_console_output()

    # Create logs directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Log initial configuration
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Logging system initialized")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {log_file.absolute()}")
    logger.info(f"Console output: {console_output}")
    logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    This is a convenience function that wraps logging.getLogger().
    Use this after setup_logging() has been called.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
