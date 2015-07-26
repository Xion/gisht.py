"""
Showing information about the gist.
"""
from __future__ import print_function

from collections import OrderedDict

from tabulate import tabulate

from gisht import logger
from gisht.gists.cache import get_gist_id
from gisht.github import get_gist_info


__all__ = ['show_gist_info']


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
