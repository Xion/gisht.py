"""
Module containing gist operations' code.
"""
from __future__ import print_function, unicode_literals

from collections import OrderedDict
import os
from pathlib import Path
import sys
import webbrowser

import envoy
from tabulate import tabulate

from gisht import BIN_DIR, GISTS_DIR, logger
from gisht.github import get_gist_info, iter_gists
from gisht.util import ensure_path, error, fatal


__all__ = [
    'run_gist', 'output_gist_binary_path', 'print_gist',
    'open_gist_page', 'show_gist_info',

    'gist_exists', 'download_gist', 'update_gist',
]


def run_gist(gist, args=()):
    """Run the gist specified by owner/name string.

    This function does not return, because the whole process
    is replaced by the gist's executable.

    :param args: Arguments to pass to the gist
    """
    logger.info("running gist %s ...", gist)

    cmd = bytes(BIN_DIR / gist)
    try:
        os.execv(cmd, [cmd] + list(args))
    except OSError as e:
        if e.errno == 8:  # Exec format error
            # TODO(xion): deduce correct interpreter based on extension
            # of the symlinks target or the MIME type from GitHub
            error("can't run gist %s -- does it have a proper hashbang?", gist)
        else:
            raise


def output_gist_binary_path(gist):
    """Print the bath to gist binary."""
    print(BIN_DIR / gist)


def print_gist(gist):
    """Print the source code of the gist specified by owner/name string."""
    logger.debug("showing source code for gist %s", gist)

    # resolve the gist exec symlink to find the source file
    # TODO(xion): what about other possible files?
    gist_exec = (BIN_DIR / gist).resolve()
    if gist_exec.exists():
        logger.debug("executable for gist %s found at %s", gist, gist_exec)
    else:
        # TODO(xion): inconsistent state; we should detect those and clean up
        fatal("executable for gist %s missing!", gist, exitcode=os.EX_SOFTWARE)

    with gist_exec.open() as f:
        sys.stdout.write(f.read())


def open_gist_page(gist):
    """Open the gist's GitHub page in the default web browser."""
    logger.debug("opening GitHub page for gist %s...", gist)

    gist_id = get_gist_id(gist)
    gist_info = get_gist_info(gist_id)

    url = gist_info.get('html_url')
    if not url:
        fatal("unable to determine the URL of gist %s...", gist)

    webbrowser.open_new_tab(url)


#: Mapping of gist --info labels to keys in the GitHub API response
#: that describes a gist. Used when displaying information abou a gist.
GIST_INFO_FIELDS = OrderedDict([
    ("ID", 'id'),
    ("Owner", ('owner', 'login')),
    ("URL", 'html_url'),  # URL to gist's user-facing page
    ("Description", 'description'),
    ("Files", ('files', list)),
    ("Created at", 'created_at'),
    ("Comments #", 'comments'),
    ("Forks #", ('forks', len)),
    ("Revisions #", ('history', len)),
    ("Last update", 'updated_at'),
])


def show_gist_info(gist):
    """Shows information about the gist specified by owner/name string."""
    logger.debug("fetching information about gist %s ...", gist)

    gist_id = get_gist_id(gist)
    gist_info = get_gist_info(gist_id)
    logger.info('information about gist %s retrieved successfully', gist)

    # prepare the gist information for display
    info = []
    for label, field in GIST_INFO_FIELDS.items():
        if not isinstance(field, tuple):
            field = (field,)
        data = gist_info
        for step in field:
            data = step(data) if callable(step) else data[step]
        if isinstance(data, list):
            data = ", ".join(data)
        info.append((label, data))

    # print it all as a table
    table = tabulate(((label, ": " + str(value)) for label, value in info),
                     tablefmt='plain')
    print(table)


# Downloading & caching

def gist_exists(gist):
    """Checks if the gist specified by owner/name string exists."""
    gist_exec_symlink = BIN_DIR / gist
    return gist_exec_symlink.exists()  # also checks if symlink is not broken


def get_gist_id(gist):
    """Convert the gist specified by owner/name to gist ID."""
    if not gist_exists(gist):
        fatal("unknown gist %s")

    gist_exec = (BIN_DIR / gist).resolve()
    gist_id = gist_exec.parent.name
    logger.debug("gist %s found to have ID=%s", gist, gist_id)

    return gist_id


def download_gist(gist):
    """Download the gist specified by owner/name string.

    :return: Whether the gist has been successfully downloaded
    """
    logger.debug("downloading gist %s ...", gist)

    owner, gist_name = gist.split('/', 1)
    for gist_json in iter_gists(owner):
        # GitHub names gists after their first files in alphabetical order
        # TODO(xion): warn the user when this could create problems,
        # i.e. when a single owner has two separate gists named the same way
        filename = list(sorted(gist_json['files'].keys()))[0]
        if filename != gist_name:
            continue

        # the gist should be placed inside a directory named after its ID
        clone_needed = True
        gist_dir = GISTS_DIR / str(gist_json['id'])
        if gist_dir.exists():
            # this is an inconsistent state, as it means the binary
            # for a gist is missing, while the repository is not;
            # no real harm in that, but we should report it anyway
            logger.warning("gist %s already downloaded")
            clone_needed = False

        # clone it if necessary (which is usually the case)
        if clone_needed:
            logger.debug("gist %s found, cloning its repository...", gist)
            ensure_path(gist_dir)
            git_clone_run = run('git clone %s %s' % (
                gist_json['git_pull_url'], gist_dir))
            if git_clone_run.status_code != 0:
                logger.warning(
                    "cloning repository for gist %s failed (exitcode %s)",
                    gist, git_clone_run.status_code)
                join(git_clone_run)
            logger.debug("gist %s successfully cloned", gist)

        # make sure the gist executable is, in fact, executable
        # TODO(xion): fix the hashbang while we're at it
        gist_exec = gist_dir / filename
        gist_exec.chmod(int('755', 8))
        logger.debug("gist file %s made executable", gist_exec)

        # create symlink from BIN_DIR/<owner>/<gist_name>
        # to the gist's executable file
        gist_owner_bin_dir = BIN_DIR / owner
        ensure_path(gist_owner_bin_dir)
        gist_link = gist_owner_bin_dir / filename
        if not gist_link.exists():
            gist_link.symlink_to(path_vector(from_=gist_link, to=gist_exec))
            logger.debug("symlinked gist 'binary' %s to executable %s",
                         gist_link, gist_exec)

        if clone_needed:
            logger.info("gist %s downloaded sucessfully", gist)
        return True

    return False


def update_gist(gist):
    """Pull the latest version of the gist specified by owner/name string.

    :return: Whether the gist has been successfully updated
    """
    logger.debug("updating gist %s ...", gist)

    gist_id = get_gist_id(gist)
    gist_dir = GISTS_DIR / gist_id
    git_pull_run = run('git pull', cwd=str(gist_dir))
    if git_pull_run.status_code != 0:
        # TODO(xion): detect conflicts and do `git reset --merge` automatically
        logger.warning("pulling changes to gist %s failed (exitcode %s)",
                       gist, git_pull_run.status_code)
        join(git_pull_run)
    logger.info("gist %s successfully updated", gist)

    return True


# Utility functions

def run(cmd, *args, **kwargs):
    """Wrapper around ``envoy.run`` that ensures the passed command string
    is NOT Unicode string, but a plain buffer of bytes.

    This is necessary to fix some Envoy's command parsing malfeasances.
    """
    return envoy.run(bytes(cmd), *args, **kwargs)


def join(process):
    """Join the process, i.e. pipe its output to our own standard stream
    and relay its exit code back to the system.

    :param process: envoy's process result object
    """
    sys.stdout.write(process.std_out)
    sys.stderr.write(process.std_err)
    raise SystemExit(process.status_code)


def path_vector(from_, to):
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
