"""
logger.py
Centralised logging factory for the pipeline.

Why use logging instead of print():
  • print() has no severity levels — you cannot distinguish INFO from ERROR
    without grepping for keywords in the text.
  • logging records include timestamps, module names, and levels by default,
    making log files machine-parseable and grep-friendly.
  • Log levels can be changed at runtime (e.g. DEBUG in dev, WARNING in prod)
    without touching any business logic.
  • Python's logging module is zero-dependency and ships with every Python install.
"""

import logging
import sys

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a named, stdout-bound logger.

    Calling get_logger() multiple times with the same name is safe —
    Python's logging module is a global registry, so the same object
    is returned and handlers are not duplicated.

    Parameters
    ----------
    name  : module name (pass __name__ or a human-readable label)
    level : minimum severity to emit; default INFO
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_FORMATTER)
        logger.addHandler(handler)
        logger.setLevel(level)
        # Prevent records from bubbling to the root logger and printing twice
        logger.propagate = False
    return logger
