#!/usr/bin/env python
"""
gisht

* This program is free software, see LICENSE file for details. *
"""
from __future__ import print_function, unicode_literals

import argparse
import os
from pathlib import Path
import sys


# TODO(xion): split into more modules


__version__ = "0.0.3"
__description__ = "Gists in the shell"
__author__ = "Karol Kuczmarski"
__license__ = "GPLv3"


#: Main application's directory.
APP_DIR = Path(os.path.expanduser('~/.gisht'))

#: Directory where gist repos are stored.
#: Subdirectories have names corresponding to numerical IDs of the gists.
GISTS_DIR = APP_DIR / 'gists'

#: Directory where links to gist "binaries" are stored.
#: Subdirectories have names corresponding to GitHub user handles
#: and contain symbolic links to executable files inside gist repos.
BIN_DIR = APP_DIR / 'bin'


# Command line arguments

def parse_argv(argv):
    """Parse command line arguments.

    :param argv: List of command line argument strings,
                 *including* the program name in argv[0]

    :return: Parse result from :func:`argparse.ArgumentParser.parse_args`
    """
    # treat everything after -- in the command line as arguments to be passed
    # to the gist executable itself (rather than be parsed by us)
    gist_args = []
    if '--' in argv:
        double_dash_pos = len(argv) - 1 - argv[::-1].index('--')  # last occur.
        gist_args = argv[double_dash_pos + 1:]
        argv = argv[:double_dash_pos]

    parser = create_argv_parser()

    # TODO(xion): support reading default parameter values from ~/.gishtrc
    result = parser.parse_args(argv[1:])
    result.gist_args = gist_args
    return result


def create_argv_parser():
    """Create a :class:`argparse.ArgumentParser` object
    for parsing command line arguments passed by the user.
    """
    parser = argparse.ArgumentParser(
        description="Download & run GitHub gists with a single command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="%(prog)s [<flags>] GIST [-- GIST_ARGS]",
        add_help=False,
    )
    gist_group = parser.add_argument_group("Gist-related")
    misc_group = parser.add_argument_group("Miscellaneous")

    def gist(value):
        """Converter/validator for the GIST command line argument."""
        try:
            owner, gist_name = value.split('/')
        except ValueError:
            raise argparse.ArgumentTypeError(
                "%r is not a valid gist reference; "
                "try '<owner>/`<name>`" % (value,))
        if owner and gist_name:
            return value
        else:
            raise argparse.ArgumentTypeError(
                "neither gist owner or name can be empty (got %r)" % (value,))
    gist_group.add_argument('gist', type=gist,
                            help="gist to run, specified as <owner>/<name> "
                                 "(e.g. Octocat/foo)",
                            metavar="GIST")
    gist_group.add_argument('-l', '--local', '--cached',
                            default=False, action='store_true',
                            help="only run the gist if it's available locally "
                                 "(do not fetch it from GitHub)")
    # TODO(xion): add a command line flag to always fetch the gist
    # (removing the existing one if necessary, or doing a `git pull`)

    gist_action_group = gist_group.add_mutually_exclusive_group()
    gist_action_group.set_defaults(run=True)
    gist_action_group.add_argument(
        '-r', '--run', dest='run', action='store_true',
        help="run specified gist; this is the default behavior, "
             "making specifying this flag optional")
    gist_action_group.add_argument(
        '-p', '--print', dest='run', action='store_false',
        help="print gist source to standard output instead of running it")

    misc_group.add_argument('--version', action='version', version=__version__)
    misc_group.add_argument('-h', '--help', action='help',
                            help="show this help message and exit")

    return parser


# Utility functions

def _ensure_path(path):
    """Ensures given path exists, creating all necessary directory levels.
    Does nothing otherwise.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)
