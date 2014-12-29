"""
Module implementing requests to GitHub API.
"""
from collections import OrderedDict
from datetime import datetime, timedelta
import pickle

from hammock import Hammock
import requests

from gisht import CACHE_DIR


__all__ = ['get_gist_info', 'iter_gists']


def get_gist_info(gist_id):
    """Retrieve information about gist of given ID.

    :param gist_id: Numerical ID of a GitHub gist
                    (NOT the user-visible <owner>/<name> string!)

    :return: Dictionary with gist information
    :raises: :class:`requests.exception.HTTPError`
    """
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

            for gist_json in _json(gists_response):
                yield gist_json

            gists_url = gists_response.links.get('next', {}).get('url')

    return generator()


class GitHub(Hammock):
    """Client for GitHub REST API."""
    API_URL = 'https://api.github.com'

    #: Size of the GitHub response page in items (e.g. gists).
    RESPONSE_PAGE_SIZE = 50

    #: Directory where the request cache is stored,
    #: relative to application's main cache directory.
    CACHE_DIR = CACHE_DIR / 'github'

    #: Time the responses will be cached.
    CACHE_TTL = timedelta(days=7)

    def __init__(self, *args, **kwargs):
        super(GitHub, self).__init__(self.API_URL, *args, **kwargs)

    def _path(self):
        """Return only the path portion of the URL."""
        result = "/" if self._append_slash else ""
        path_comp = self
        while path_comp._parent:
            result = "/" + path_comp._name + result
            path_comp = path_comp._parent
        return result[1:] if len(result) > 1 else result  # no leading slash

    def _request(self, method, *args, **kwargs):
        """Make the HTTP request using :module:`requests` module."""
        use_cache = kwargs.pop('cache', True)

        # try to load the response from cache, if available
        if use_cache:
            if not self.CACHE_DIR.exists():
                self.CACHE_DIR.mkdir(parents=True)
            cached_response_file = self.CACHE_DIR / self._chain(*args)._path()
            if not self._expired(cached_response_file):
                with cached_response_file.open('rb') as f:
                    return pickle.load(f)

        response = super(GitHub, self)._request(method, *args, **kwargs)

        # save the obtained response to cache
        if use_cache:
            if not cached_response_file.parent.exists():
                cached_response_file.parent.mkdir(parents=True)
            with cached_response_file.open('wb') as f:
                pickle.dump(response, f)

        return response

    def _expired(self, cached_response_file):
        """Check whether the cached response has expired."""
        if not cached_response_file.exists():
            return True
        last_modify_timestamp = cached_response_file.stat().st_mtime
        last_modify_time = datetime.fromtimestamp(last_modify_timestamp)
        return last_modify_time + self.CACHE_TTL <= datetime.now()


# Utility functions

def _json(response):
    """Interpret given Requests' response object as JSON."""
    return response.json(object_pairs_hook=OrderedDict)
