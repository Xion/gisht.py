"""
Tests for the various data types used through the application.
"""
from contextlib import contextmanager

from taipan.testing import TestCase

import gisht.data as __unit__


class Gist(TestCase):
    """Tests for :class:`~gisht.data.Gist`."""
    OWNER = 'Grinch'
    NAME = 'stealChristmas'
    ID = 'z9y8x7w6v5u4t3s2r1'

    WRONG_HOST = 'www.example.com'
    NOT_A_GIST = 'Alice has a cat'

    def test_ctor__ref(self):
        gist = __unit__.Gist(self.OWNER + '/' + self.NAME)

        self.assertEquals(self.OWNER, gist.owner)
        self.assertEquals(self.NAME, gist.name)

    def test_ctor__ref__invalid(self):
        ref = 'a/b/c'
        with self.assert_gist_error("not", "valid", "reference", ref):
            __unit__.Gist(ref)

    def test_ctor__url(self):
        url = 'http://%s/%s/%s' % (__unit__.GITHUB_GISTS_HOST,
                                   self.OWNER, self.ID)
        gist = __unit__.Gist(url)

        self.assertEquals(url, str(gist.url))
        self.assertEquals(self.OWNER, gist.owner)
        self.assertEquals(self.ID, gist.id)

    def test_ctor__url__wrong_host(self):
        with self.assert_gist_error("unrecognized", "URL", self.WRONG_HOST):
            __unit__.Gist('http://' + self.WRONG_HOST)

    def test_ctor__url__malformed_path(self):
        path = 'a/b/c'
        with self.assert_gist_error("invalid", path):
            __unit__.Gist('http://%s/%s' % (__unit__.GITHUB_GISTS_HOST, path))

    def test_ctor__owner_name(self):
        gist = __unit__.Gist(self.OWNER, self.NAME)

        self.assertEquals(self.OWNER, gist.owner)
        self.assertEquals(self.NAME, gist.name)

    def test_ctor__owner_name__empty(self):
        with self.assert_gist_error("empty", self.OWNER):
            __unit__.Gist(self.OWNER, '')

    def test_ctor__invalid_format(self):
        with self.assert_gist_error("unrecognized", self.NOT_A_GIST):
            __unit__.Gist(self.NOT_A_GIST)

    # Utility functions

    @contextmanager
    def assert_gist_error(self, *args):
        with self.assertRaises(__unit__.GistError) as r:
            yield r

        msg = str(r.exception)
        for arg in args:
            self.assertIn(arg, msg)
