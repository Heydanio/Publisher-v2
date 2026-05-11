"""Logger structure avec couleurs ANSI."""
import logging
import sys


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        record.levelname_colored = f"{color}{record.levelname:8s}{self.RESET}"
        return super().format(record)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Cree un logger configure."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler(sys.stdout)

    if sys.stdout.isatty():
        formatter = ColoredFormatter(
            '%(asctime)s | %(levelname_colored)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
