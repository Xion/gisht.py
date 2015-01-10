"""
Module with logic for generating autocomplete suggestions
to command line arguments.
"""
import argcomplete
import requests

from gisht import BIN_DIR
from gisht.github import iter_gists


__all__ = [
    'trigger',
    'gist_completer',
]


def trigger(parser):
    """Trigger autocomplete for given :class:`ArgumentParser`,
    if the application was invoked for this purpose.
    """
    argcomplete.autocomplete(parser)


def gist_completer(prefix, parsed_args, **kwargs):
    """Autocompleter for the GIST command line argument.

    It tries to complete the gist identifier (<owner>/<name>) by listing
    all the gists for the typed <owner>, possibly filtered
    through a prefix of <name>.

    :return: Iterable of possible completions
    """
    results = set()

    # start with the locally available gists, possibly including entries
    # for GitHub users whose gists we have cached (if autocomplete prefix
    # does not include a slash)
    for entry in BIN_DIR.rglob('*'):
        entry = '/'.join(entry.relative_to(BIN_DIR).parts)
        if not entry.startswith(prefix):
            continue
        if '/' not in entry:
            entry = entry + '/'
        results.add(entry)
    # TODO(xion): the above is somewhat redundant in typical case, when GitHub
    # is available and user typed the owner part fully; elide it in this case

    # if username was given in full, query GitHub for that user's gist
    # and include them in the suggestions
    local = getattr(parsed_args, 'local', False)
    if '/' in prefix and not local:
        owner, name_prefix = prefix.split('/')
        try:
            for gist_json in iter_gists(owner):  # TODO(xion): cache this LOL
                for filename in gist_json['files'].keys():
                    if filename.startswith(name_prefix):
                        results.add(owner + '/' + filename)
                        break  # only add one (first) file per gist
        except requests.exceptions.HTTPError:
            pass  # limit to local completions if GitHub is unreachable

    return sorted(results)
