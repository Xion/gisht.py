"""
Module containing gist operations' code.
"""
import os
from pathlib import Path
import sys

import envoy

from gisht import _ensure_path, BIN_DIR
from gisht.github import iter_gists


__all__ = [
    'run_gist', 'print_gist',
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


def print_gist(gist):
    """Print the source code of the gist specified by owner/name string."""
    gist_exec = (BIN_DIR / gist).resolve()
    with gist_exec.open() as f:
        sys.stdout.write(f.read())


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


# Utility functions

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
