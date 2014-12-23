"""
Tests for the gisht.py script.
"""
import json
import os

from requests.exceptions import HTTPError
import responses
from taipan.collections import dicts
from taipan.strings import is_string
from taipan.testing import before, after, TestCase

import gisht as __unit__


# TODO(xion): add more tests


# GitHub API tests

class _GitHubApi(TestCase):
    """Base class for test cases for code interacting with GitHub API."""
    @before
    def activate_responses(self):
        responses.mock.__enter__()

    @after
    def deactive_responses(self):
        responses.mock.__exit__()


class IterGists(_GitHubApi):
    USER = 'JohnDoe'

    NOT_FOUND_RESPONSE = {
        "message": "Not Found",
        "documentation_url": "https://developer.github.com/v3",
    }

    def test_none(self):
        with self.assertRaises(TypeError):
            __unit__.iter_gists(None)

    def test_user_not_found(self):
        self._stub_gists_response(
            self.USER, self.NOT_FOUND_RESPONSE, status=404)

        with self.assertRaises(HTTPError) as r:
            list(__unit__.iter_gists(self.USER))
        self.assertEquals(404, r.exception.response.status_code)

    def test_no_gists(self):
        self._stub_gists_response(self.USER, [])
        self.assertEmpty(__unit__.iter_gists(self.USER))

    # Utility functions

    def _stub_gists_response(self, user, response_json, status=None):
        if not is_string(response_json):
            response_json = json.dumps(response_json)

        url = str(__unit__.GitHub().users(user).gists)
        kwargs = dicts.AbsentDict({
            'body': response_json,
            'content_type': 'application/vnd.github.v3+json',
            'status': status or dicts.ABSENT,
        })
        responses.add(responses.GET, url, **kwargs)


# Utility functions tests

class PathVector(TestCase):
    PATH = '/foo/bar'

    def test_noop(self):
        result = __unit__._path_vector(self.PATH, self.PATH)
        self.assertEquals('.', str(result))
