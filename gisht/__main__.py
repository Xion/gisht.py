#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""
Executable script.
"""
from __future__ import print_function

import logging
import os
import sys

import requests

from gisht import APP_DIR, flags, logger
from gisht.args import parse_argv
from gisht.args.data import GistCommand
from gisht.gists import (download_gist, gist_exists, update_gist,
                         open_gist_page, output_gist_binary_path,
                         print_gist, run_gist, show_gist_info)
from gisht.util import error


def main(argv=sys.argv):
    """Entry point."""
    if os.name != 'posix':
        print("only POSIX operating systems are supported", file=sys.stderr)
        return os.EX_UNAVAILABLE

    args = parse_argv(argv, flags)
    setup_logging(args.log_level)

    # during the first run, display a warning about executing untrusted code
    if not APP_DIR.exists():
        if logger.getEffectiveLevel() >= logging.WARNING:
            acknowledged = display_warning()
            if not acknowledged:
                return 2
        APP_DIR.mkdir(parents=True)

    gist = args.gist
    gist_args = args.gist_args

    # download it from GitHub, if the gist hasn't been cached locally,
    # or update it to latest revision if user requested that
    if gist_exists(gist):
        logger.debug("gist %s found among already downloaded gists", gist)
        if args.local is False:
            if not update_gist(gist):
                error("failed to update gist %s")
    else:
        if args.local:
            error("gist %s is not available locally", gist,
                  exitcode=os.EX_NOINPUT)
        try:
            if not download_gist(gist):
                error("gist %s not found", gist, exitcode=os.EX_DATAERR)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                error("user '%s' not found", gist.split('/')[0],
                      exitcode=os.EX_UNAVAILABLE)
            else:
                error("HTTP error: %s", e, exitcode=os.EX_UNAVAILABLE)

    # do with the gist what the user has requested (default: run it)
    if args.command == GistCommand.RUN:
        run_gist(gist, gist_args)
    elif args.command not in GistCommand:
        error("unknown gist action %r", args.command, exitcode=os.EX_USAGE)
    else:
        if gist_args:
            error("gist arguments are only allowed when running the gist",
                  exitcode=os.EX_USAGE)
        if args.command == GistCommand.WHICH:
            output_gist_binary_path(gist)
        elif args.command == GistCommand.PRINT:
            print_gist(gist)
        elif args.command == GistCommand.OPEN:
            open_gist_page(gist)
        elif args.command == GistCommand.INFO:
            show_gist_info(gist)


def setup_logging(level):
    """Sets up the application-wide logging system to output everything to
    standard error stream, and filter our own messages according to given
    minimum level.
    """
    logger.setLevel(level)

    # propagate log messages from our application-specific logger
    # to the root logger, to be dumped to stderr alongside any possible output
    # from other loggers (like those from third party libraries)
    logger.propagate = True
    handler = logging.StreamHandler(sys.stderr)
    logging.getLogger().addHandler(handler)


def display_warning():
    """Displays a warning about executing untrusted code
    and ask the user to continue.
    :return: Whether the user chose to continue
    """
    print(
        "WARNING: gisht is used to download & run code from a remote source.",
        "",
        "Never run gists that you haven't authored, and/or do not trust.",
        "Doing so is dangerous, and may expose your system to security risks!",
        "",
        "(If you continue, this warning won't be shown again).",
        "",
        sep=os.linesep, file=sys.stderr)

    print("Do you want to continue? [y/N]: ", end="", file=sys.stderr)
    try:
        answer = raw_input()
    except NameError:
        answer = input()  # Python 3
    return answer.lower().strip() == 'y'


if __name__ == '__main__':
    sys.exit(main() or 0)
