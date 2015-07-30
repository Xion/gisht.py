"""
Test package.
"""
from contextlib import contextmanager
try:
    from StringIO import StringIO  # Python 2.x
except ImportError:
    from io import StringIO  # Python 3.x
import sys

from taipan.testing import TestCase as _TestCase


__all__ = ['TestCase']


class TestCase(_TestCase):
    """Base class for tests with some convenience methods."""

    @contextmanager
    def assertExit(self, code=None):
        """Assert that application would exit after executing given code."""
        # run the code, capturing stdout and stderr
        try:
            sys.stdout = stdout = StringIO()
            sys.stderr = stderr = StringIO()
            with self.assertRaises(SystemExit) as r:
                yield r
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        # assert on exit ocode
        if code is not None:
            if code is True:
                code = 0
            elif code is False:
                code = -1
            self.assertEquals(code, r.exception.code)

        # store the content of standard streams for possible further assertion
        r.stdout = stdout.getvalue()
        r.stderr = stderr.getvalue()
