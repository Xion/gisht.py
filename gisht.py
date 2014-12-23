#!/usr/bin/env python
"""
gisht
"""
from __future__ import print_function, unicode_literals

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

    gist_exec_symlink = BIN_DIR / argv[1]
    if gist_exec_symlink.exists():
        # TODO(xion): check if the symlink is not broken
        gist_run = _run(gist_exec_symlink)
        return gist_run.status_code

    if not GISTS_DIR.exists():
        GISTS_DIR.mkdir(parents=True)

    owner, gist_name = argv[1].split('/', 1)
    for gist_json in iter_gists(owner):
        for filename in gist_json['files'].keys():
            if filename == gist_name:
                gist_dir = GISTS_DIR / str(gist_json['id'])
                if not gist_dir.exists():
                    gist_dir.mkdir()
                git_clone_run = _run('git clone %s %s' % (
                    gist_json['git_pull_url'], gist_dir))
                if git_clone_run.status_code != 0:
                    print(git_clone_run.std_err, file=sys.stderr)
                    return git_clone_run.status_code
                # TODO(xion): symlink main file in BIN_DIR
                # TODO(xion): run the gist
                return 0
    print("Gist %s/%s not found" % (owner, gist_name))
    return 1


# GitHub API

class GitHub(Hammock):
    """Client for GitHub REST API."""
    API_URL = 'https://api.github.com'

    #: Size of the GitHub response page in items (e.g. gists).
    RESPONSE_PAGE_SIZE = 50

    def __init__(self, *args, **kwargs):
        super(GitHub, self).__init__(self.API_URL, *args, **kwargs)


def iter_gists(owner):
    """Iterate over gists owned by given user.

    :param owner: GitHub user's name
    :return: Iterable (generator) of parsed JSON objects (dictionaries)
    :raises: :class:`requests.exception.HTTPError`
    """
    def generator():
        github = GitHub()
        gists_url = str(github.users(owner).gists)
        while gists_url:
            gists_response = requests.get(
                gists_url, params={'per_page': GitHub.RESPONSE_PAGE_SIZE})
            gists_response.raise_for_status()

            for gist_json in _json(gists_response):
                yield gist_json

            gists_url = gists_response.links.get('next', {}).get('url')

    return generator()


# Utility functions

def _run(cmd, *args, **kwargs):
    """Wrapper around ``envoy.run`` that ensures the passed command string
    is NOT Unicode string, but a plain buffer of bytes.

    This is necessary to fix some Envoy's command parsing malfeasances.
    """
    return envoy.run(bytes(cmd), *args, **kwargs)


def _json(response):
    """Interpret given Requests' response object as JSON."""
    return response.json(object_pairs_hook=OrderedDict)


if __name__ == '__main__':
    sys.exit(main() or 0)
