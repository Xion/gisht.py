"""
Tests for command-line handling code.
"""
import argparse
from contextlib import contextmanager
try:
    from StringIO import StringIO  # Python 2.x
except ImportError:
    from io import StringIO  # Python 3.x
import sys

from taipan.testing import before, expectedFailure, TestCase

import gisht.args as __unit__
from gisht.args.data import GistCommand
from gisht.args.parser import LogLevelAction


class ParseArgv(TestCase):
    PROG = 'gisht'

    GIST = 'Example/gist'

    DEFAULT_LOG_LEVEL = LogLevelAction.DEFAULT_LEVEL

    def test_empty(self):
        with self._assertExit(2) as r:
            self._invoke()
        self.assertEmpty(r.stdout)
        self.assertIn("usage", r.stderr)

    def test_help(self):
        for flag in ('-h', '--help'):
            with self._assertExit(0) as r:
                self._invoke(flag)

            self.assertEmpty(r.stderr)  # expecting help output on stdout

            self.assertIn("usage", r.stdout)
            # help flags are not shown in usage, so this is one way
            # of asserting that help was displayed
            # TODO(xion): add epilog= to ArgumentParser and assert on that
            self.assertIn(flag, r.stdout)

    def test_gist__invalid__no_slash(self):
        invalid_gist = self.GIST.replace('/', '')

        with self._assertExit(2) as r:
            self._invoke(invalid_gist)

        self.assertIn("usage", r.stderr)
        self.assertIn(invalid_gist, r.stderr)

    def test_gist__invalid__trailing_slash(self):
        invalid_gist = self.GIST[:self.GIST.find('/') + 1]

        with self._assertExit(2) as r:
            self._invoke(invalid_gist)

        self.assertIn("usage", r.stderr)
        self.assertIn(invalid_gist, r.stderr)

    def test_gist__valid(self):
        args = self._invoke(self.GIST)
        self.assertEquals(self.GIST, args.gist)

    def test_command__default(self):
        args = self._invoke(self.GIST)
        self.assertEquals(GistCommand.RUN, args.command)

    def test_command__explicit__short(self):
        args = self._invoke('-r', self.GIST)
        self.assertEquals(GistCommand.RUN, args.command)

    def test_command__explicit__long(self):
        args = self._invoke('--run', self.GIST)
        self.assertEquals(GistCommand.RUN, args.command)

    @expectedFailure
    def test_action__multiple__duplicate(self):
        # supplying the same action flag multiple times makes no sense
        # and should be illegal. Unfortunately, there is no way to tell that
        # to the ArgumentParser :-(
        with self._assertExit(2) as r:
            self._invoke('-r', '-r', self.GIST)

        self.assertIn("usage", r.stderr)
        self.assertIn('-r', r.stderr)

    def test_action__multiple__distinct(self):
        with self._assertExit(2) as r:
            self._invoke('-r', '-p', self.GIST)

        self.assertIn("usage", r.stderr)
        self.assertIn('-r', r.stderr)
        self.assertIn('-p', r.stderr)

    def test_logging__intensify(self):
        verbose_level = self._invoke('-v', self.GIST).log_level
        self.assertLess(verbose_level, self.DEFAULT_LOG_LEVEL)

    def test_logging__dampen(self):
        quiet_level = self._invoke('-q', self.GIST).log_level
        self.assertGreater(quiet_level, self.DEFAULT_LOG_LEVEL)

    # TODO(xion): add more tests for real argument sets

    def _invoke(self, *args):
        return __unit__.parse_argv([self.PROG] + list(args))

    @contextmanager
    def _assertExit(self, code=None):
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


class CreateArgvParser(TestCase):

    @before
    def invoke(self):
        self.result = __unit__.create_argv_parser()

    def test_parser_class(self):
        self.assertIsInstance(self.result, argparse.ArgumentParser)

    def test_usage__mentions_gist_args(self):
        self.assertIn("--", self.result.usage)

    def test_usage__omits_cruft(self):
        self.assertNotIn("-h", self.result.usage)
        self.assertNotIn("--help", self.result.usage)
        self.assertNotIn("--version", self.result.usage)
