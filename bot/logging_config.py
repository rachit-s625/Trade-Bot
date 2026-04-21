"""
Logging configuration for the trading bot.
Sets up both file and console handlers with structured formatting.
"""

import logging
import logging.handlers
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure structured logging to both console and rotating file.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured root logger
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers on repeated calls
    if root_logger.handlers:
        root_logger.handlers.clear()

    # --- File handler (rotating, max 5 MB, keep 3 backups) ---
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # capture everything to file
    root_logger.addHandler(file_handler)

    # --- Console handler (INFO and above) ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    root_logger.info("Logging initialised | file=%s", LOG_FILE)
    return root_logger
