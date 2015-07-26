"""
Tests for the functions for downloading gists and caching them locally.
"""
import mock
from taipan.testing import TestCase

import gisht.gists.cache as __unit__


class DownloadGist(TestCase):
    GIST = 'JohnDoe/foo'

    @mock.patch.object(__unit__, 'iter_gists')
    def test_not_found__no_gists(self, mock_iter_gists):
        mock_iter_gists.return_value = ()
        self.assertFalse(__unit__.download_gist(self.GIST))

    @mock.patch.object(__unit__, 'iter_gists')
    def test_not_found__not_present(self, mock_iter_gists):
        mock_iter_gists.return_value = [
            self._gist_json('foo', 'bar'),
            self._gist_json('abc', 'xyz'),
        ]
        self.assertFalse(__unit__.download_gist(self.GIST))

    # TODO(xion): write tests for the (semi-)successful cases

    def _gist_json(self, owner, name, **kwargs):
        # there has to be an entry in the 'files' dictionary
        # that corresponds to gist name; the actual content of it is not used
        files = dict.fromkeys(kwargs.pop('files', ()), 'unused')
        files.setdefault(name, 'unused')

        result = kwargs.copy()
        result['files'] = files
        return result
