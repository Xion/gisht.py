"""
Module containing gist operations' code.
"""
import os
import sys

from gisht import _ensure_path, _join, _path_vector, BIN_DIR, iter_gists


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
