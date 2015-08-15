#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""
Executable script.
"""
from __future__ import print_function

import logging
import os
import sys

from gisht import APP_DIR, flags, logger
from gisht.args import parse_argv
from gisht.data import GistCommand
from gisht.gists import (ensure_gist,
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

    # if we are to do something that requires cloned gist,
    # make sure it exists
    if args.command in (GistCommand.RUN,
                        GistCommand.PRINT,
                        GistCommand.WHICH) and not gist.url:
        ensure_gist(gist, local=args.local)

    # do with the gist what the user has requested (default: run it)
    if args.command == GistCommand.RUN:
        run_gist(gist, gist_args, local=args.local)
    elif args.command not in GistCommand:
        error("unknown gist action %r", args.command, exitcode=os.EX_USAGE)
    else:
        if gist_args:
            error("gist arguments are only allowed when running the gist",
                  exitcode=os.EX_USAGE)
        if gist.url:
            # TODO(xion): lift that limitation
            error("URLs are only allowed when running the gist",
                  exitcode=os.EX_USAGE)

        command_func = {
            GistCommand.WHICH: output_gist_binary_path,
            GistCommand.PRINT: print_gist,
            GistCommand.OPEN: open_gist_page,
            GistCommand.INFO: show_gist_info,
        }.get(args.command)

        assert command_func is not None, (
            "unsupported gist command: %s" % args.command)
        command_func(gist)


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
