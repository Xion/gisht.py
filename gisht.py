#!/usr/bin/env python
"""
gisht

* This program is free software, see LICENSE file for details. *
"""
from __future__ import print_function, unicode_literals

import argparse
from collections import OrderedDict
import os
from pathlib import Path
import sys

import envoy
from hammock import Hammock
import requests


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


def main(argv=sys.argv):
    """Entry point."""
    if os.name != 'posix':
        _error("only POSIX operating systems are supported",
               exitcode=os.EX_UNAVAILABLE)

    args = parse_argv(argv)

    # during the first run, display a warning about executing untrusted code
    if not APP_DIR.exists():
        if not display_warning():
            return 2
    _ensure_path(APP_DIR)

    gist = args.gist
    gist_args = args.gist_args

    # if the gist hasn't been cached locally, download it from GitHub
    if not gist_exists(gist):
        if args.local:
            _error("gist %s is not available locally", gist,
                   exitcode=os.EX_NOINPUT)
        try:
            if not download_gist(gist):
                _error("gist %s not found", gist, exitcode=os.EX_DATAERR)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                _error("user '%s' not found", gist.split('/')[0],
                       exitcode=os.EX_UNAVAILABLE)
            else:
                _error("HTTP error: %s", e, exitcode=os.EX_UNAVAILABLE)

    # do with the gist what the user has requested (default: run it)
    if args.run:
        run_gist(gist, gist_args)
    else:
        if gist_args:
            _error("gist arguments are not allowed when printing gist source",
                   exitcode=os.EX_USAGE)
        print_gist(gist)


def display_warning():
    """Displays a warning about executing untrusted code
    and ask the user to continue.
    :return: Whether the user chose to continue
    """
    print(
        "WARNING: gisht is used to download & run code from a remote source.",
        "",
        "Never run gists that you haven't authored, and/or do not trust.",
        "Doing so is dangerous, and may expose your system to security risks!",
        "",
        "(This warning won't be shown again).",
        "",
        sep=os.linesep, file=sys.stderr)

    print("Do you want to continue? [y/N]: ", end="", file=sys.stderr)
    answer = raw_input()
    return answer.lower().strip() == 'y'


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


# Gist operations

def gist_exists(gist):
    """Checks if the gist specified by owner/name string exists."""
    gist_exec_symlink = BIN_DIR / gist
    return gist_exec_symlink.exists()  # also checks if symlink is not broken


def run_gist(gist, args=()):
    """Run the gist specified by owner/name string.

    This function does not return, because the whole process
    is replaced by the gist's executable.

    :param args: Arguments to pass to the gist
    """
    # TODO(xion): check for the existence of proper shebang,
    # and if it's not there, deduce correct interpreter based on extension
    # of the symlinks target
    cmd = bytes(BIN_DIR / gist)
    os.execv(cmd, [cmd] + list(args))


def print_gist(gist):
    """Print the source code of the gist specified by owner/name string."""
    gist_exec = (BIN_DIR / gist).resolve()
    with gist_exec.open() as f:
        sys.stdout.write(f.read())


def download_gist(gist):
    """Download the gist specified by owner/name string.

    :return: Whether the gist has been successfully downloaded
    """
    # TODO(xion): make this idempotent, i.e. allowing gist to be downloaded
    # multiple times if necessary (to perform updates)

    owner, gist_name = gist.split('/', 1)
    for gist_json in iter_gists(owner):
        for filename in gist_json['files'].keys():
            if filename != gist_name:
                continue

            # clone the gist's repository into directory named after gist ID
            gist_dir = GISTS_DIR / str(gist_json['id'])
            _ensure_path(gist_dir)
            git_clone_run = _run(
                'git clone %s %s' % (gist_json['git_pull_url'], gist_dir))
            if git_clone_run.status_code != 0:
                _join(git_clone_run)

            # make sure the gist executable is, in fact, executable
            gist_exec = gist_dir / filename
            gist_exec.chmod(int('755', 8))

            # create symlink from BIN_DIR/<owner>/<gist_name>
            # to the gist's executable file
            gist_owner_bin_dir = BIN_DIR / owner
            _ensure_path(gist_owner_bin_dir)
            gist_link = gist_owner_bin_dir / filename
            gist_link.symlink_to(_path_vector(from_=gist_link, to=gist_exec))

            return True

    return False


# GitHub API

class GitHub(Hammock):
    """Client for GitHub REST API."""
    API_URL = 'https://api.github.com'

    #: Size of the GitHub response page in items (e.g. gists).
    RESPONSE_PAGE_SIZE = 50

    def __init__(self, *args, **kwargs):
        super(GitHub, self).__init__(self.API_URL, *args, **kwargs)


def iter_gists(owner):
    """Iterate over gists owned by given user.

    :param owner: GitHub user's name
    :return: Iterable (generator) of parsed JSON objects (dictionaries)
    :raises: :class:`requests.exception.HTTPError`
    """
    if type(owner).__name__ not in ('str', 'unicode'):
        raise TypeError("expected a string")

    def generator():
        github = GitHub()
        gists_url = str(github.users(owner).gists)
        while gists_url:
            gists_response = requests.get(
                gists_url, params={'per_page': GitHub.RESPONSE_PAGE_SIZE})
            gists_response.raise_for_status()

            for gist_json in _json(gists_response):
                yield gist_json

            gists_url = gists_response.links.get('next', {}).get('url')

    return generator()


# Utility functions

def _error(msg, *args, **kwargs):
    """Output an error message to stderr and end the program.
    :param exitcode: Optional keyword argument to specify the exit code
    """
    msg = msg % args if args else msg
    print("%s: error: %s" % (os.path.basename(sys.argv[0]), msg),
          file=sys.stderr)
    raise SystemExit(kwargs.pop('exitcode', 1))


def _ensure_path(path):
    """Ensures given path exists, creating all necessary directory levels.
    Does nothing otherwise.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)


def _run(cmd, *args, **kwargs):
    """Wrapper around ``envoy.run`` that ensures the passed command string
    is NOT Unicode string, but a plain buffer of bytes.

    This is necessary to fix some Envoy's command parsing malfeasances.
    """
    return envoy.run(bytes(cmd), *args, **kwargs)


def _join(process):
    """Join the process, i.e. pipe its output to our own standard stream
    and relay its exit code back to the system.

    :param process: envoy's process result object
    """
    sys.stdout.write(process.std_out)
    sys.stderr.write(process.std_err)
    raise SystemExit(process.status_code)


def _json(response):
    """Interpret given Requests' response object as JSON."""
    return response.json(object_pairs_hook=OrderedDict)


def _path_vector(from_, to):
    """Return a 'path vector' from given path to the other, i.e.
    the argument of ``cd`` that'd take the user from the source
    directly to target.
    """
    from_, to = map(Path, (from_, to))

    # TODO(xion): consider using http://stackoverflow.com/a/21499676/434799
    # instead of standard os.commonprefix (we don't run into the edge case
    # of the latter yet)
    common_prefix = os.path.commonprefix(list(map(str, (from_, to))))

    # compute the number of '..' segments that are necessary to go
    # from source up to the common prefix
    prefix_wrt_source = Path(from_).relative_to(common_prefix)
    pardir_count = len(prefix_wrt_source.parts)
    if not from_.is_dir():
        pardir_count -= 1

    # join those '..' segments with relative path from common prefix to target
    target_wrt_prefix = Path(to).relative_to(common_prefix)
    return Path(*([os.path.pardir] * pardir_count)) / target_wrt_prefix


if __name__ == '__main__':
    sys.exit(main() or 0)
