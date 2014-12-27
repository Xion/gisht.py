#!/usr/bin/env python
"""
Executable script.
"""
from __future__ import print_function

import os
import sys

import requests

from gisht import _error, _ensure_path, APP_DIR, parse_argv
from gisht.gists import download_gist, gist_exists, print_gist, run_gist


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
    _ensure_path(APP_DIR)

    gist = args.gist
    gist_args = args.gist_args

    # if the gist hasn't been cached locally, download it from GitHub
    if not gist_exists(gist):
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
    if args.run:
        run_gist(gist, gist_args)
    else:
        if gist_args:
            _error("gist arguments are not allowed when printing gist source",
                   exitcode=os.EX_USAGE)
        print_gist(gist)


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


if __name__ == '__main__':
    sys.exit(main() or 0)
