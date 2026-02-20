import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    env = os.getenv("ENV", "prod").lower()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture everything internally

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # ------------------
    # File Handler (ALWAYS DEBUG)
    # ------------------
    file_handler = RotatingFileHandler(
        "draft.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # Always log everything
    file_handler.setFormatter(formatter)

    # ------------------
    # Console Handler
    # ------------------
    console_handler = logging.StreamHandler()

    if env == "debug":
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)