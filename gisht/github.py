"""
Module implementing requests to GitHub API.
"""
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
import pickle

from hammock import Hammock
import requests

from gisht import CACHE_DIR
from gisht.util import ensure_path


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

class CachedHammock(Hammock):
    """Custom version of :class:`Hammock` REST client that supports
    caching of GET requests.
    """
    def __init__(self, *args, **kwargs):
        self._cache_dir = kwargs.pop('cache_dir', None)
        self._cache_ttl = kwargs.pop('cache_ttl', timedelta(days=7))
        super(CachedHammock, self).__init__(*args, **kwargs)

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
        use_cache = (method.upper() == 'GET' and
                     bool(self._cache_dir) and
                     kwargs.pop('cache', True))

        # try to load the response from cache, if available
        if use_cache:
            url_path = self._chain(*args)._path()
            cache_file = Path(self._cache_dir) / url_path
            if not self._expired(cache_file):
                with cache_file.open('rb') as f:
                    return pickle.load(f)

        # TODO(xion): if request has failed due to transient error,
        # return the cached response even if it's expired, and show appropriate
        # warning on stderr that data might be stale (on -i/--info)
        response = super(CachedHammock, self)._request(method, *args, **kwargs)
        # TODO(xion): the above logic should be also influenced by -/--local

        # save the obtained response to cache
        if use_cache:
            ensure_path(cache_file.parent)
            with cache_file.open('wb') as f:
                pickle.dump(response, f)

        return response

    def _expired(self, cache_file):
        """Check whether the cached response has expired."""
        if not cache_file.exists():
            return True
        last_modify_timestamp = cache_file.stat().st_mtime
        last_modify_time = datetime.fromtimestamp(last_modify_timestamp)
        return last_modify_time + self._cache_ttl <= datetime.now()


class GitHub(CachedHammock):
    """Client for GitHub REST API."""
    API_URL = 'https://api.github.com'

    #: Size of the GitHub response page in items (e.g. gists).
    RESPONSE_PAGE_SIZE = 50

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('cache_dir', CACHE_DIR / 'github')
        super(GitHub, self).__init__(self.API_URL, *args, **kwargs)


# Utility functions

def to_json(response):
    """Interpret given Requests' response object as JSON."""
    return response.json(object_pairs_hook=OrderedDict)
