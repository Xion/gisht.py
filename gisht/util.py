"""
Module with utility functions used throughout the code.
"""
import logging
import os
from pathlib import Path
import sys

from gisht import logger


__all__ = [
    'ensure_path',
    'error', 'fatal',
]


def ensure_path(path):
    """Ensures given path exists, creating all necessary directory levels.
    Does nothing otherwise.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)


# Error handling

def error(msg, *args, **kwargs):
    """Output an error message and end the program.
    :param exitcode: Optional keyword argument to specify the exit code
    """
    _exit(logging.ERROR, msg, *args, **kwargs)


def fatal(msg, *args, **kwargs):
    """Output an error message and end the program.
    :param exitcode: Optional keyword argument to specify the exit code
    """
    _exit(logging.CRITICAL, msg, *args, **kwargs)


def _exit(severity, msg, *args, **kwargs):
    """Log a message with given severity and exit the program."""
    msg = msg % args if args else msg
    logger.log(severity, "%s: error: %s", os.path.basename(sys.argv[0]), msg)
    raise SystemExit(kwargs.get('exitcode', 1))
