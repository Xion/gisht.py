"""
Tests for gist operations.
"""
from taipan.testing import TestCase

import gisht.gists as __unit__


# Utility functions

class PathVector(TestCase):
    PATH = '/foo/bar'

    def test_noop(self):
        result = __unit__._path_vector(self.PATH, self.PATH)
        self.assertEquals('.', str(result))
