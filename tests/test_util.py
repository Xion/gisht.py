"""
Tests for utility functions.
"""
from taipan.testing import TestCase

import gisht.util as __unit__


class PathVector(TestCase):
    PATH = '/foo/bar'

    def test_noop(self):
        result = __unit__.path_vector(self.PATH, self.PATH)
        self.assertEquals('.', str(result))
