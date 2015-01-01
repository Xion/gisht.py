"""
Module containing gist operations' code.
"""
from __future__ import print_function, unicode_literals

from collections import OrderedDict
import os
from pathlib import Path
import sys

import envoy
from tabulate import tabulate

from gisht import BIN_DIR, GISTS_DIR
from gisht.github import get_gist_info, iter_gists
from gisht.util import ensure_path


__all__ = [
    'run_gist', 'output_gist_binary_path', 'print_gist', 'show_gist_info',
    'gist_exists', 'download_gist',
]


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


def output_gist_binary_path(gist):
    """Print the bath to gist binary."""
    print(BIN_DIR / gist)


def print_gist(gist):
    """Print the source code of the gist specified by owner/name string."""
    gist_exec = (BIN_DIR / gist).resolve()
    with gist_exec.open() as f:
        sys.stdout.write(f.read())


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
    gist_exec = (BIN_DIR / gist).resolve()
    gist_id = gist_exec.parent.name
    gist_info = get_gist_info(gist_id)

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
            ensure_path(gist_dir)
            git_clone_run = run('git clone %s %s' % (
                gist_json['git_pull_url'], gist_dir))
            if git_clone_run.status_code != 0:
                join(git_clone_run)

            # make sure the gist executable is, in fact, executable
            gist_exec = gist_dir / filename
            gist_exec.chmod(int('755', 8))

            # create symlink from BIN_DIR/<owner>/<gist_name>
            # to the gist's executable file
            gist_owner_bin_dir = BIN_DIR / owner
            ensure_path(gist_owner_bin_dir)
            gist_link = gist_owner_bin_dir / filename
            gist_link.symlink_to(path_vector(from_=gist_link, to=gist_exec))

            return True

    return False


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
