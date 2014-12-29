"""
Module for parsing command line arguments.
"""
import argparse
from enum import Enum

from gisht import __version__


__all__ = ['parse_argv', 'GistAction']


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


class GistAction(Enum):
    """Action to undertake towards the gist."""
    RUN = 'run'
    PRINT = 'print'
    INFO = 'info'


# Argument parser creation

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
    gist_action_group.set_defaults(action=GistAction.RUN)
    gist_action_group.add_argument(
        '-r', '--run', dest='action',
        action='store_const', const=GistAction.RUN,
        help="run specified gist; this is the default behavior, "
             "making specifying this flag optional")
    gist_action_group.add_argument(
        '-p', '--print', dest='action',
        action='store_const', const=GistAction.PRINT,
        help="print gist source to standard output instead of running it")
    gist_action_group.add_argument(
        '-i', '--info', dest='action',
        action='store_const', const=GistAction.INFO,
        help="show summary information about the specified gist")

    misc_group.add_argument('--version', action='version', version=__version__)
    misc_group.add_argument('-h', '--help', action='help',
                            help="show this help message and exit")

    return parser
