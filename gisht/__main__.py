#!/usr/bin/env python
"""
Executable script.
"""
from __future__ import print_function

import os
import sys

import requests

from gisht import APP_DIR
from gisht.args import GistAction, parse_argv
from gisht.gists import (
    download_gist, gist_exists,
    output_gist_binary_path, print_gist, run_gist, show_gist_info)


def main(argv=sys.argv):
    """Entry point."""
    if os.name != 'posix':
        _error("only POSIX operating systems are supported",
               exitcode=os.EX_UNAVAILABLE)

    args = parse_argv(argv)

    # during the first run, display a warning about executing untrusted code
    if not APP_DIR.exists():
        if not display_warning():
            return 2
        APP_DIR.mkdir(parents=True)

    gist = args.gist
    gist_args = args.gist_args

    # if the gist hasn't been cached locally, download it from GitHub
    if args.action != GistAction.INFO and not gist_exists(gist):
        if args.local:
            _error("gist %s is not available locally", gist,
                   exitcode=os.EX_NOINPUT)
        try:
            if not download_gist(gist):
                _error("gist %s not found", gist, exitcode=os.EX_DATAERR)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                _error("user '%s' not found", gist.split('/')[0],
                       exitcode=os.EX_UNAVAILABLE)
            else:
                _error("HTTP error: %s", e, exitcode=os.EX_UNAVAILABLE)

    # do with the gist what the user has requested (default: run it)
    if args.action == GistAction.RUN:
        run_gist(gist, gist_args)
    elif args.action not in GistAction:
        _error("unknown gist action %r" % (args.action,), exitcode=os.EX_USAGE)
    else:
        if gist_args:
            _error("gist arguments are only allowed when running the gist",
                   exitcode=os.EX_USAGE)
        if args.action == GistAction.WHICH:
            output_gist_binary_path(gist)
        elif args.action == GistAction.PRINT:
            print_gist(gist)
        elif args.action == GistAction.INFO:
            show_gist_info(gist)


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
        "(This warning won't be shown again).",
        "",
        sep=os.linesep, file=sys.stderr)

    print("Do you want to continue? [y/N]: ", end="", file=sys.stderr)
    answer = raw_input()
    return answer.lower().strip() == 'y'


# Utility functions

def _error(msg, *args, **kwargs):
    """Output an error message to stderr and end the program.
    :param exitcode: Optional keyword argument to specify the exit code
    """
    msg = msg % args if args else msg
    print("%s: error: %s" % (os.path.basename(sys.argv[0]), msg),
          file=sys.stderr)
    raise SystemExit(kwargs.pop('exitcode', 1))


if __name__ == '__main__':
    sys.exit(main() or 0)
