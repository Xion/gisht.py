"""
Module implementing requests to GitHub API.
"""
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
import pickle

from hammock import Hammock
import requests

from gisht import CACHE_DIR, flags, logger
from gisht.args.data import GistCommand
from gisht.util import ensure_path, error


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
        path_component = self
        while path_component._parent:
            result = "/" + path_component._name + result
            path_component = path_component._parent
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
            if self._expired(cache_file):
                rv = self._on_cache_miss(url_path)
                if rv is not None:
                    return rv
            else:
                with cache_file.open('rb') as f:
                    cached_response = pickle.load(f)

                # register the cache hit and possibly modify cached response
                rv = self._on_cache_hit(url_path, cached_response)
                if rv is not False:
                    return cached_response if rv in (None, True) else rv

        # issue the request if we couldn't find a cached response
        try:
            response = super(CachedHammock, self) \
                ._request(method, *args, **kwargs)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RetryError):
            # if the request has failed due to transient error,
            # by default return the cached response even if it's expired
            if use_cache and cache_file.exists():
                with cache_file.open('rb') as f:
                    cached_response = pickle.load(f)
                rv = self._on_cache_rescue(url_path, cached_response)
                if rv is not False:
                    return cached_response if rv in (None, True) else rv
            raise

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

    # Caching-related to events
    # (to override in subclasses, if desired)

    def _on_cache_miss(self, path):
        """Invoked when given ``path`` does not have a cached response.

        :return: Anything other than ``None`` will be used in lieu
                 of the cached response (but it will **not** be saved
                 in the actual cache).
        """

    def _on_cache_hit(self, path, content):
        """Invoked when given request ``path`` has a non-stale ``content``
        that can be returned as a response to the request.

        :return: ``True`` or ``None`` if ``content`` shall be used as response.
                 ``False`` if cache shall not be used for this request at all.
                 Any other value will replace ``content`` as the response.
        """

    def _on_cache_rescue(self, path, content):
        """Invoked when given request ``path`` cannot be accessed due
        to network connectivity error, but there is cached ``content``
        available.

        :return: ``True`` or ``None`` if ``content`` shall be used as response.
                 ``False`` if the error shall be propagated.
                 Any other value will replace ``content`` as the response.
        """


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
