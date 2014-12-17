#!/usr/bin/env python
"""
gisht
"""
from __future__ import print_function

from collections import OrderedDict
import os
from pathlib import Path
import sys

import envoy
from hammock import Hammock
import requests


__version__ = "0.0.1"
__description__ = "Gists in the shell"
__author__ = "Karol Kuczmarski"
__license__ = "Simplified BSD"


#: Main application's directory.
APP_DIR = Path(os.path.expanduser('~/.gisht'))

#: Directory where gist repos are stored.
#: Subdirectories have names corresponding to numerical IDs of the gists.
GISTS_DIR = APP_DIR / 'gists'

#: Directory where links to gist "binaries" are stored.
#: Subdirectories have names corresponding to GitHub user handles
#: and contain symbolic links to executable files inside gist repos.
BIN_DIR = APP_DIR / 'bin'


def main(argv=sys.argv):
    """Entry point."""
    if len(argv[1:]) == 0:
        print("No gist specified.", file=sys.stderr)
        return 1

    gist_exec_symlink = GISTS_DIR / argv[1]
    if gist_exec_symlink.exists():
        # TODO(xion): check if the symlink is not broken
        gist_run = envoy.run(str(gist_exec_symlink))
        return gist_run.status_code

    # TODO(xion): extract to separate function and support paging
    owner, gist_name = argv[1].split('/', 1)
    github = GitHub()
    gists_response = requests.get(str(github.users(owner).gists))
    gists_response.raise_for_status()
    for gist_json in _json(gists_response):
        for filename in gist_json['files'].keys():
            if filename == gist_name:
                # TODO(xion): ensure the GISTS_DIR path exists
                git_clone_run = envoy.run('git clone %s %s' % (
                    gist_json['git_pull_url'],
                    GISTS_DIR / str(gist_json['id'])))
                if git_clone_run.status_code != 0:
                    print(git_clone_run.std_err, file=sys.stderr)
                    return git_clone_run.status_code
                # TODO(xion): symlink main file in BIN_DIR
                # TODO(xion): run the gist
                return 0
    print("Gist %s/%s not found" % (owner, gist_name))
    return 1


class GitHub(Hammock):
    """Client for GitHub REST API."""
    API_URL = 'https://api.github.com'

    def __init__(self, *args, **kwargs):
        super(GitHub, self).__init__(self.API_URL, *args, **kwargs)


# Utility functions

def _json(response):
    """Interpret given Requests' response object as JSON."""
    return response.json(object_pairs_hook=OrderedDict)


if __name__ == '__main__':
    sys.exit(main() or 0)
