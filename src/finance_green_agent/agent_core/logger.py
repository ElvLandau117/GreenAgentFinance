import logging
import os
from datetime import datetime

GREEN = "\x1b[32;20m"
GREY = "\x1b[38;20m"
YELLOW = "\x1b[33;20m"
RED = "\x1b[31;20m"
BOLD_RED = "\x1b[31;1m"
BOLD = "\x1b[1m"
RESET = "\x1b[0m"

BASE = "%(asctime)s"
LEVEL = "%(levelname)s"
NAME = "-- %(name)s:"
MSG = "%(message)s"

CONSOLE_FORMAT = " ".join((LEVEL, NAME, MSG))
FILE_FORMAT = " ".join((BASE, LEVEL, NAME, MSG))

is_verbose = os.environ.get("FINANCE_GREEN_VERBOSE", "0") == "1"
MAX_MESSAGE_LENGTH = 20000 if is_verbose else 1000

LOGS_DIR = os.path.join("logs", "raw")
os.makedirs(LOGS_DIR, exist_ok=True)


def color(color_value):
    colored_str = "".join((color_value, LEVEL, RESET))
    bold_str = "".join((BOLD, NAME, RESET))
    return " ".join((colored_str, bold_str, MSG))


class ColorFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: color(GREY),
        logging.INFO: color(GREEN),
        logging.WARNING: color(YELLOW),
        logging.ERROR: color(RED),
        logging.CRITICAL: color(BOLD_RED),
    }

    def format(self, record):
        if len(record.msg) > MAX_MESSAGE_LENGTH and not is_verbose:
            record.msg = record.msg[:MAX_MESSAGE_LENGTH] + "... [truncated]"

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class TruncatingFormatter(logging.Formatter):
    def format(self, record):
        if len(record.msg) > MAX_MESSAGE_LENGTH and not is_verbose:
            record.msg = record.msg[:MAX_MESSAGE_LENGTH] + "... [truncated]"
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False

    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColorFormatter())
        logger.addHandler(console_handler)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(LOGS_DIR, f"{name}_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(TruncatingFormatter(FILE_FORMAT))
        logger.addHandler(file_handler)

    return logger
