"""
Module for parsing command line arguments.
"""
import argparse
from enum import Enum
from itertools import chain
import logging

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
    WHICH = 'which'
    PRINT = 'print'
    INFO = 'info'


# Argument parser creation

def create_argv_parser():
    """Create a :class:`argparse.ArgumentParser` object
    for parsing command line arguments passed by the user.
    """
    parser = argparse.ArgumentParser(
        description="Download & run GitHub gists straight from the terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)

    gist_group = parser.add_argument_group(
        "Gist", "Specifies the gist, optionally with flags")

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
                            help="GitHub gist, specified as <owner>/<name> "
                                 "(e.g. Octocat/foo)",
                            metavar="GIST")
    gist_group.add_argument('-l', '--local', '--cached',
                            default=False, action='store_true',
                            help="only run the gist if it's available locally "
                                 "(do not fetch it from GitHub)")
    # TODO(xion): add a command line flag to always fetch the gist
    # (removing the existing one if necessary, or doing a `git pull`)

    gist_action_group = parser.add_argument_group(
        "Actions", "Possible actions to perform on the gist") \
        .add_mutually_exclusive_group()
    gist_action_group.set_defaults(action=GistAction.RUN)
    gist_action_group.add_argument(
        '-r', '--run', dest='action',
        action='store_const', const=GistAction.RUN,
        help="run specified gist; this is the default behavior "
             "if no action was specified explicitly")
    gist_action_group.add_argument(
        '-w', '--which', dest='action',
        action='store_const', const=GistAction.WHICH,
        help="output the path to binary which would be ran for given gist; "
             "useful for passing it to other commands via $( )")
    gist_action_group.add_argument(
        '-p', '--print', dest='action',
        action='store_const', const=GistAction.PRINT,
        help="print gist source on the standard output")
    gist_action_group.add_argument(
        '-i', '--info', dest='action',
        action='store_const', const=GistAction.INFO,
        help="show summary information about the specified gist")

    log_group = parser.add_argument_group(
        "Verbosity", "Only errors are printed by default") \
        .add_mutually_exclusive_group()
    log_group.set_defaults(log_level=logging.ERROR)
    log_group.add_argument('-v', '--verbose', dest='log_level',
                           action=LogLevelAction,
                           const=-LogLevelAction.DEFAULT_INCREMENT,
                           help="include finer grained details in the output; "
                                "this option can be specified multiple times")
    log_group.add_argument('-q', '--quiet', dest='log_level',
                           action=LogLevelAction,
                           const=LogLevelAction.DEFAULT_INCREMENT,
                           help="decrease the verbosity level")

    misc_group = parser.add_argument_group("Miscellaneous", "Other options")
    misc_group.add_argument('--version', action='version', version=__version__)
    misc_group.add_argument('-h', '--help', action='help',
                            help="show this help message and exit")

    # get the autogenerated usage string and tweak it a little
    # to include gist arguments that are handled separately
    # and exclude the miscellaneous flags which aren't part of a normal usage
    usage = parser.format_usage()
    usage = usage[usage.find(parser.prog):].rstrip("\n")  # remove cruft
    for misc_flag in chain.from_iterable(a.option_strings
                                         for a in misc_group._group_actions):
        usage = usage.replace(" [%s]" % misc_flag, "")
    parser.usage = usage + " [-- GIST_ARGS]"
    return parser


class LogLevelAction(argparse.Action):
    """Custom argument parser's :class:`Action` for handling
    log level / verbosity flags.
    """
    DEFAULT_LEVEL = logging.INFO
    DEFAULT_INCREMENT = 10
    DEFAULT_MINIMUM = logging.NOTSET
    DEFAULT_MAXIMUM = logging.CRITICAL

    def __init__(self, *args, **kwargs):
        self.min = kwargs.pop('min', self.DEFAULT_MINIMUM)
        self.max = kwargs.pop('max', self.DEFAULT_MAXIMUM)
        kwargs.setdefault('const', self.DEFAULT_INCREMENT)
        super(LogLevelAction, self).__init__(*args, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        current = getattr(namespace, self.dest, self.DEFAULT_LEVEL)
        # TODO(xion): error-out if the limits are exceeded
        new = max(self.min, min(self.max, current + self.const))
        setattr(namespace, self.dest, new)
