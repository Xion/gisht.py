#!/usr/bin/env python
"""
gisht

* This program is free software, see LICENSE file for details. *
"""
__version__ = "0.6-dev"
__description__ = "Gists in the shell"
__author__ = "Karol Kuczmarski"
__license__ = "GPLv3"


import argparse
import logging
import os
from pathlib import Path


#: Main application's directory.
APP_DIR = Path(os.path.expanduser('~/.gisht'))

#: Directory where gist repos are stored.
#: Subdirectories have names corresponding to numerical IDs of the gists.
GISTS_DIR = APP_DIR / 'gists'

#: Directory where links to gist "binaries" are stored.
#:
#: Subdirectories have names corresponding to GitHub user handles
#: and contain symbolic links to executable files inside gist repos.
BIN_DIR = APP_DIR / 'bin'

#: Directory where the request cache resides.
#:
#: Subdirectories contain pickled :class:`Response` objects
#: (from :module:`requests`) inside directory paths corresponding to URL paths.
CACHE_DIR = APP_DIR / 'cache'


#: Logger object used by the application.
logger = logging.getLogger(__name__)

#: Flags given to the application in the command line.
flags = argparse.Namespace()
