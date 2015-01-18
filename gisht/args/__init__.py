"""
Package for handling command line arguments.
"""
from gisht.args import autocomplete
from gisht.args.parser import create_argv_parser


__all__ = ['parse_argv']


def parse_argv(argv, namespace=None):
    """Parse command line arguments.

    :param argv: List of command line argument strings,
                 *including* the program name in argv[0]
    :param namespace: `argparse`\ 's :class:`Namespace` object
                      to fill with parsed arguments

    :return: Parse result from :func:`argparse.ArgumentParser.parse_args`
    """
    # treat everything after -- in the command line as arguments to be passed
    # to the gist executable itself (rather than be parsed by us)
    # TODO(xion): implement this as custom argparse action with nargs=REMAINDER
    gist_args = []
    if '--' in argv:
        double_dash_pos = len(argv) - 1 - argv[::-1].index('--')  # last occur.
        gist_args = argv[double_dash_pos + 1:]
        argv = argv[:double_dash_pos]

    parser = create_argv_parser()

    # trigger autocompletion, unless gist args have been provided after --
    # (otherwise they may be considered as part of GIST argument)
    # TODO(xion): make ArgumentParser handle GIST_ARGS and remove this hack
    if not gist_args:
        autocomplete.trigger(parser)

    # TODO(xion): support reading default parameter values from ~/.gishtrc
    result = parser.parse_args(argv[1:], namespace)
    result.gist_args = gist_args
    return result
