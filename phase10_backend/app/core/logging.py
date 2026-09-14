"""
Structured application logging.

Logs API requests, simulation/optimization lifecycle events, and failures.
Never logs sensitive information (no secrets, no raw request bodies).
"""
import logging
import sys


def configure_logging(debug: bool = True) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO

    logger = logging.getLogger("passive_shelter_api")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = configure_logging()
