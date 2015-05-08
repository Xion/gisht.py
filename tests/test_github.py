"""
GitHub API tests.
"""
from contextlib import contextmanager
import json

from requests.exceptions import HTTPError
import responses
from taipan.collections import dicts
from taipan.strings import is_string
from taipan.testing import before, after, TestCase

from gisht import flags
import gisht.github as __unit__


class _GitHubApi(TestCase):
    """Base class for test cases for code interacting with GitHub API."""
    MIME_TYPE = 'application/vnd.github.v3+json'

    NOT_FOUND_RESPONSE = {
        "message": "Not Found",
        "documentation_url": "https://developer.github.com/v3",
    }

    @before
    def set_flags(self):
        flags.local = False

    @before
    def activate_responses(self):
        responses.mock.__enter__()

    @after
    def deactivate_responses(self):
        responses.mock.__exit__()

    def _stub_response(self, url, response_json, status=None):
        if not is_string(response_json):
            response_json = json.dumps(response_json)

        kwargs = dicts.AbsentDict({
            'body': response_json,
            'content_type': self.MIME_TYPE,
            'status': status or dicts.ABSENT,
        })
        responses.add(responses.GET, str(url), **kwargs)

    @contextmanager
    def _assert404(self):
        with self.assertRaises(HTTPError) as r:
            yield r
        self.assertEquals(404, r.exception.response.status_code)


class GetGistInfo(_GitHubApi):
    GIST_ID = '42'

    def test_gist_not_found(self):
        self._stub_gist_response(
            self.GIST_ID, self.NOT_FOUND_RESPONSE, status=404)

        with self._assert404():
            __unit__.get_gist_info(self.GIST_ID)

    def _stub_gist_response(self, gist_id, response_json, status=None):
        self._stub_response(__unit__.GitHub().gists(gist_id),
                            response_json, status)


class IterGists(_GitHubApi):
    USER = 'JohnDoe'

    def test_none(self):
        with self.assertRaises(TypeError):
            __unit__.iter_gists(None)

    def test_user_not_found(self):
        self._stub_gists_response(
            self.USER, self.NOT_FOUND_RESPONSE, status=404)

        with self._assert404():
            list(__unit__.iter_gists(self.USER))

    def test_no_gists(self):
        self._stub_gists_response(self.USER, [])
        self.assertEmpty(__unit__.iter_gists(self.USER))

    # TODO(xion): add tests for typical case when user has gists

    def _stub_gists_response(self, user, response_json, status=None):
        self._stub_response(__unit__.GitHub().users(user).gists,
                            response_json, status)
