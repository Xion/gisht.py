"""
Tests for command-line handling code.
"""
import argparse

from taipan.testing import before, TestCase

import gisht.args as __unit__


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
