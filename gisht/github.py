"""
Module implementing requests to GitHub API.
"""
from collections import OrderedDict

import requests

from gisht import CACHE_DIR, flags, logger
from gisht.args.data import GistCommand
from gisht.ext import CachedHammock
from gisht.util import error


__all__ = ['get_gist_info', 'iter_gists']


def get_gist_info(gist_id):
    """Retrieve information about gist of given ID.

    :param gist_id: Numerical ID of a GitHub gist
                    (NOT the user-visible <owner>/<name> string!)

    :return: Dictionary with gist information
    :raises: :class:`requests.exception.HTTPError`
    """
    if '/' in gist_id:
        raise ValueError("expected gist ID, not the <owner>/<name> reference!")

    github = GitHub()
    response = github.gists.GET(gist_id)
    response.raise_for_status()
    return response.json()


def iter_gists(owner):
    """Iterate over gists owned by given user.

    :param owner: GitHub user's name
    :return: Iterable (generator) of parsed JSON objects (dictionaries)
    :raises: :class:`requests.exception.HTTPError`
    """
    if type(owner).__name__ not in ('str', 'unicode'):
        raise TypeError("expected a string")

    def generator():
        github = GitHub()
        gists_url = str(github.users(owner).gists)
        while gists_url:
            gists_response = requests.get(
                gists_url, params={'per_page': GitHub.RESPONSE_PAGE_SIZE})
            gists_response.raise_for_status()

            for gist_json in to_json(gists_response):
                yield gist_json

            gists_url = gists_response.links.get('next', {}).get('url')

    return generator()


# API client

class GitHub(CachedHammock):
    """Client for GitHub REST API."""
    API_URL = 'https://api.github.com'

    #: Size of the GitHub response page in items (e.g. gists).
    RESPONSE_PAGE_SIZE = 50

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cache_dir', CACHE_DIR / 'github')
        super(GitHub, self).__init__(self.API_URL, *args, **kwargs)

    def _on_cache_miss(self, path):
        if flags.local:
            error("can't access GitHub path /%s in --local mode", path)

    def on_cache_hit(self, path, content):
        if flags.local is False:
            return False  # bypass the cache

    def _on_cache_rescue(self, path, content):
        if flags.command == GistCommand.INFO:
            logger.warning(
                "could not communicate with GitHub -- "
                "gist information may be out of date")


# Utility functions

def to_json(response):
    """Interpret given Requests' response object as JSON."""
    return response.json(object_pairs_hook=OrderedDict)
