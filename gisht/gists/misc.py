"""
Miscellneous operations on the gists.
"""
from __future__ import print_function

import os
import sys
import webbrowser

from gisht import BIN_DIR, logger
from gisht.gists.cache import get_gist_id
from gisht.github import get_gist_info
from gisht.util import fatal


__all__ = [
    'output_gist_binary_path',
    'print_gist',
    'open_gist_page',
]


def output_gist_binary_path(gist):
    """Print the bath to gist binary."""
    print(BIN_DIR / gist)


def print_gist(gist):
    """Print the source code of the gist specified by owner/name string."""
    logger.debug("showing source code for gist %s", gist)

    # resolve the gist exec symlink to find the source file
    # TODO(xion): what about other possible files?
    gist_exec = (BIN_DIR / gist).resolve()
    if gist_exec.exists():
        logger.debug("executable for gist %s found at %s", gist, gist_exec)
    else:
        # TODO(xion): inconsistent state; we should detect those and clean up
        fatal("executable for gist %s missing!", gist, exitcode=os.EX_SOFTWARE)

    with gist_exec.open() as f:
        sys.stdout.write(f.read())


def open_gist_page(gist):
    """Open the gist's GitHub page in the default web browser."""
    logger.debug("opening GitHub page for gist %s...", gist)

    gist_id = get_gist_id(gist)
    gist_info = get_gist_info(gist_id)

    url = gist_info.get('html_url')
    if not url:
        fatal("unable to determine the URL of gist %s...", gist)

    webbrowser.open_new_tab(url)
