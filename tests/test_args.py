"""
Tests for command-line handling code.
"""
import argparse
import sys

from taipan.testing import before, expectedFailure, skipIf, skipUnless

import gisht.args as __unit__
from gisht.args.parser import LogLevelAction
from gisht.data import GistCommand
from tests import TestCase


class ParseArgv(TestCase):
    PROG = 'gisht'

    GIST = 'Example/gist'

    DEFAULT_LOG_LEVEL = LogLevelAction.DEFAULT_LEVEL

    def test_empty(self):
        with self.assertExit(2) as r:
            self._invoke()
        self.assertEmpty(r.stdout)
        self.assertIn("usage", r.stderr)

    def test_help(self):
        for flag in ('-h', '--help'):
            with self.assertExit(0) as r:
                self._invoke(flag)

            self.assertEmpty(r.stderr)  # expecting help output on stdout

            self.assertIn("usage", r.stdout)
            # help flags are not shown in usage, so this is one way
            # of asserting that help was displayed
            # TODO(xion): add epilog= to ArgumentParser and assert on that
            self.assertIn(flag, r.stdout)

    def test_gist__invalid__no_slash(self):
        invalid_gist = self.GIST.replace('/', '')

        with self.assertExit(2) as r:
            self._invoke(invalid_gist)

        self.assertIn("usage", r.stderr)
        self.assertIn(invalid_gist, r.stderr)

    def test_gist__invalid__trailing_slash(self):
        invalid_gist = self.GIST[:self.GIST.find('/') + 1]

        with self.assertExit(2) as r:
            self._invoke(invalid_gist)

        self.assertIn("usage", r.stderr)
        self.assertIn(invalid_gist, r.stderr)

    def test_gist__valid(self):
        args = self._invoke(self.GIST)
        self.assertEquals(self.GIST, args.gist.ref)

    def test_command__default(self):
        args = self._invoke(self.GIST)
        self.assertEquals(GistCommand.RUN, args.command)

    def test_command__explicit__short(self):
        args = self._invoke('-r', self.GIST)
        self.assertEquals(GistCommand.RUN, args.command)

    def test_command__explicit__long(self):
        args = self._invoke('--run', self.GIST)
        self.assertEquals(GistCommand.RUN, args.command)

    def do_test_action__multiple__duplicate(self):
        # Supplying the same action flag multiple times makes no sense
        # and should be illegal.
        with self.assertExit(2) as r:
            self._invoke('-r', '-r', self.GIST)

        self.assertIn("usage", r.stderr)
        self.assertIn('-r', r.stderr)

    # Unfortunately, argparse below Python 3.4 doesn't seem to think so.
    @skipIf(sys.version_info >= (3, 4), "requires Python 3.4+")
    @expectedFailure
    def test_action__multiple__duplicate__py2(self):
        self.do_test_action__multiple__duplicate()

    @skipUnless(sys.version_info >= (3, 4), "requires Python <3.4")
    def test_action__multiple__duplicate__p34(self):
        self.do_test_action__multiple__duplicate()

    def test_action__multiple__distinct(self):
        with self.assertExit(2) as r:
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
