"""
Functions for downloading gists and caching them locally.
"""
import os
import stat

import requests

from gisht import BIN_DIR, GISTS_DIR, logger
from gisht.github import iter_gists
from gisht.util import ensure_path, error, fatal, join, run


# TODO(xion): clean the list up, we don't need to export so much anymore
__all__ = [
    'gist_exists', 'get_gist_id',
    'ensure_gist', 'download_gist', 'update_gist',
]


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


def ensure_gist(gist, local=False):
    """Ensure that given gist is downloaded & cached.

    :param gist: Gist as owner/name string

    This, of course, may mean downloading the gist if it hasn't been before,
    or doing nothing if it has.
    """
    if gist_exists(gist):
        logger.debug("gist %s found among already downloaded gists", gist)
        if local is False:
            # take the opportunity to update the gist to latest revision
            if not update_gist(gist):
                error("failed to update gist %s")
    else:
        if local:
            error("gist %s is not available locally", gist,
                  exitcode=os.EX_NOINPUT)
        try:
            if not download_gist(gist):
                error("gist %s not found", gist, exitcode=os.EX_DATAERR)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                error("user '%s' not found", gist.split('/')[0],
                      exitcode=os.EX_UNAVAILABLE)
            else:
                error("HTTP error: %s", e, exitcode=os.EX_UNAVAILABLE)


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
                logger.error(
                    "cloning repository for gist %s failed (exitcode %s)",
                    gist, git_clone_run.status_code)
                join(git_clone_run)
            logger.debug("gist %s successfully cloned", gist)

        # make sure the gist executable is, in fact, executable
        # TODO(xion): fix the hashbang while we're at it
        gist_exec = gist_dir / filename
        gist_exec.chmod(GIST_EXEC_PERMISSIONS)
        logger.debug("adjusted permissions for gist file %s", gist_exec)

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

#: Permission bits we set on the gist executable.
GIST_EXEC_PERMISSIONS = (
    stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
    stat.S_IWUSR |
    stat.S_IXUSR | stat.S_IXGRP
)


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
