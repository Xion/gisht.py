#!/usr/bin/env python
"""
gisht

* This program is free software, see LICENSE file for details. *
"""
import os
from pathlib import Path


# TODO(xion): split into more modules


__version__ = "0.0.3"
__description__ = "Gists in the shell"
__author__ = "Karol Kuczmarski"
__license__ = "GPLv3"


#: Main application's directory.
APP_DIR = Path(os.path.expanduser('~/.gisht'))

#: Directory where gist repos are stored.
#: Subdirectories have names corresponding to numerical IDs of the gists.
GISTS_DIR = APP_DIR / 'gists'

#: Directory where links to gist "binaries" are stored.
#: Subdirectories have names corresponding to GitHub user handles
#: and contain symbolic links to executable files inside gist repos.
BIN_DIR = APP_DIR / 'bin'


# Utility functions

def _ensure_path(path):
    """Ensures given path exists, creating all necessary directory levels.
    Does nothing otherwise.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)
