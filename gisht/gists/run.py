"""
Logic for running the gists as executable programs.
"""
import os
from pathlib import Path
from pipes import quote as shell_quote
from shlex import split as shell_split

import requests

from gisht import BIN_DIR, logger
from gisht.data import Gist
from gisht.gists.cache import ensure_gist
from gisht.github import get_gist_info
from gisht.util import error


__all__ = ['run_gist']


def run_gist(gist, args=(), local=False):
    """Run the specified gist."""
    if gist.url:
        return run_gist_url(gist, args, local=local)
    elif gist.ref:
        return run_named_gist(gist, args)
    else:
        raise ValueError("unrecognized gist format")


def run_gist_url(gist, args=(), local=False):
    """Run the gist specified by an URL.

    If successful, this function does not return.

    :param gist: Gist as :class:`Gist` object
    :param args: Arguments to pass to the gist
    :param local: Whether to only run gists that are available locally
    """
    try:
        gist_info = get_gist_info(gist.id)
    except requests.exceptions.HTTPError:
        error("couldn't retrieve GitHub gist %s/%s", gist.owner, gist.id)

    # warn if the actual gist owner is different than the one in the URL;
    # TODO(xion): consider asking for confirmation;
    # there may be some phishing scenarios possible here
    owner = gist_info.get('owner', {}).get('login')
    if gist.owner != owner:
        logger.warning("gist %s is owned by %s, not %s",
                       gist.id, owner, gist.owner)

    gist_name = list(sorted(gist_info['files'].keys()))[0]
    actual_gist_ref = '/'.join((owner, gist_name))

    ensure_gist(actual_gist_ref, local=local)
    return run_named_gist(actual_gist_ref, args)


def run_named_gist(gist, args=()):
    """Run the gist specified by owner/name string.

    This function does not return, because the whole process
    is replaced by the gist's executable.

    :param gist: Gist as :class:`Gist` object or <owner>/<name> string
    :param args: Arguments to pass to the gist
    """
    if isinstance(gist, Gist):
        gist = gist.ref

    logger.info("running gist %s ...", gist)

    executable = bytes(BIN_DIR / gist)
    try:
        os.execv(executable, [executable] + list(args))
    except OSError as e:
        if e.errno != 8:  # Exec format error
            raise

        logger.warning("couldn't run gist %s directly -- "
                       "does it have a proper hashbang?", gist)

        # try to figure out the interpreter to use based on file extension
        # contained within the gist name
        extension = Path(gist).suffix
        if not extension:
            # TODO(xion): use MIME type from GitHub as additional hint
            # as to the choice of interpreter
            error("can't deduce interpreter for gist %s "
                  "without file extension", gist)
        interpreter = COMMON_INTERPRETERS.get(extension)
        if not interpreter:
            error("no interpreter found for extension '%s'", extension)

        # format an interpreter-specific command line
        # and execute it within current process (hence the argv shenanigans)
        cmd = interpreter % dict(script=str(BIN_DIR / gist),
                                 args=' '.join(map(shell_quote, args)))
        cmd_argv = shell_split(cmd)
        os.execvp(cmd_argv[0], cmd_argv)


#: Mapping of common interpreters from file extensions they can handle.
#:
#: Interpreters are defined as shell commands with placeholders for gist
#: script name and its arguments.
COMMON_INTERPRETERS = {
    '.hs': 'runhaskell %(script)s %(args)s',
    '.js': 'node -e %(script)s %(args)s',
    '.pl': 'perl -- %(script)s %(args)s',
    '.py': 'python %(script)s - %(args)s',
    '.rb': 'irb -- %(script)s %(args)s',
    '.sh': 'sh -- %(script)s %(args)s',
}
