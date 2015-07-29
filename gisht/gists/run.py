"""
Logic for running the gists as executable programs.
"""
import os
from pathlib import Path
from pipes import quote as shell_quote
from shlex import split as shell_split

from furl import furl
import requests

from gisht import BIN_DIR, logger
from gisht.gists.cache import ensure_gist
from gisht.github import get_gist_info
from gisht.util import error


__all__ = ['run_gist']


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


def run_gist(gist, args=(), local=False):
    """Run the specified gist."""
    gist = furl(gist)
    if gist.host:
        return run_gist_url(gist, args, local=local)
    else:
        gist = str(gist.path)
        return run_named_gist(gist, args)


def run_gist_url(gist, args=(), local=False):
    """Run the gist specified by an URL.

    If successful, this function does not return.

    :param gist: Gist URL as furl object
    :param args: Arguments to pass to the gist
    :param local: Whether to only run gists that are available locally
    """
    if gist.host != GITHUB_GISTS_HOST:
        error("unrecognized gist URL domain: %s", gist.host)

    try:
        owner, gist_id = gist.path.segments
    except ValueError:
        error("invalid format GitHub gist URL")

    try:
        gist_info = get_gist_info(gist_id)
    except requests.exceptions.HTTPError:
        error("couldn't retrieve GitHub gist %s/%s", owner, gist_id)

    # warn if the actual gist owner is different than the one in the URL;
    # TODO(xion): consider asking for confirmation;
    # there may be some phishing scenarios possible here
    fetched_owner = gist_info.get('owner', {}).get('login')
    if owner != fetched_owner:
        logger.warning("gist %s is owned by %s, not %s",
                        gist_id, fetched_owner, owner)

    gist_name = list(sorted(gist_info['files'].keys()))[0]
    actual_gist = '/'.join((fetched_owner, gist_name))

    ensure_gist(actual_gist, local=local)
    return run_named_gist(actual_gist, args)

#: Host part of the GitHub gists' URLs.
GITHUB_GISTS_HOST = 'gist.github.com'


def run_named_gist(gist, args=()):
    """Run the gist specified by owner/name string.

    This function does not return, because the whole process
    is replaced by the gist's executable.

    :param args: Arguments to pass to the gist
    """
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
