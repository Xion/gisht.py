"""
Module with utility functions used throughout the code.
"""
import logging
import os
from pathlib import Path
import sys

import envoy

from gisht import logger


__all__ = [
    'ensure_path', 'path_vector',
    'run', 'join',
    'error', 'fatal',
]


# Directory path functions

def ensure_path(path):
    """Ensures given path exists, creating all necessary directory levels.
    Does nothing otherwise.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)


def path_vector(from_, to):
    """Return a 'path vector' from given path to the other, i.e.
    the argument of ``cd`` that'd take the user from the source
    directly to target.
    """
    from_, to = map(Path, (from_, to))

    # TODO(xion): consider using http://stackoverflow.com/a/21499676/434799
    # instead of standard os.commonprefix (we don't run into the edge case
    # of the latter yet)
    common_prefix = os.path.commonprefix(list(map(str, (from_, to))))

    # compute the number of '..' segments that are necessary to go
    # from source up to the common prefix
    prefix_wrt_source = Path(from_).relative_to(common_prefix)
    pardir_count = len(prefix_wrt_source.parts)
    if not from_.is_dir():
        pardir_count -= 1

    # join those '..' segments with relative path from common prefix to target
    target_wrt_prefix = Path(to).relative_to(common_prefix)
    return Path(*([os.path.pardir] * pardir_count)) / target_wrt_prefix


# Processes

def run(cmd, *args, **kwargs):
    """Wrapper around ``envoy.run`` that ensures the passed command string
    is NOT Unicode string, but a plain buffer of bytes.

    This is necessary to fix some Envoy's command parsing malfeasances.
    """
    return envoy.run(bytes(cmd), *args, **kwargs)


def join(process):
    """Join the process, i.e. pipe its output to our own standard stream
    and relay its exit code back to the system.

    :param process: envoy's process result object
    """
    sys.stdout.write(process.std_out)
    sys.stderr.write(process.std_err)
    raise SystemExit(process.status_code)


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
