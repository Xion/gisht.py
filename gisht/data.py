"""
Module defining data types used throughout the application.
"""
from enum import Enum

from furl import furl


__all__ = [
    'Gist', 'GistError',
    'GistCommand',
]


class Gist(object):
    """Represents a single gist.

    Every property of the gist is optional. Depending on how :class:`Gist`
    object has been initialized, some or even all of them may be present,
    though.
    """
    __slots__ = ('_id', '_name', '_owner', '_url')

    #: URL to the GitHub page of the gist.
    url = property(lambda self: self._url)

    #: Name of the GitHub user who owns the gist.
    owner = property(lambda self: self._owner)

    #: Gist name.
    #:
    #: Coupled with ``owner``, this is a MOSTLY unique identifier of the gist.
    #: However, since gist name is derived from a filename within the gist,
    #: it IS possible for a single owner to have two gists with the same name.
    name = property(lambda self: self._name)

    #: Unique identifier of the gist in GitHub.
    id = property(lambda self: self._id)

    def __init__(self, *args):
        """Constructor.

        Accept either a single argument that's a gist ID or URL,
        or two arguments: owner & gist name.
        """
        self._url = None
        self._owner = None
        self._name = None
        self._id = None

        if len(args) == 1:
            self._init_from_ref(args[0])
        elif len(args) == 2:
            self._init_from_name(*args)
        else:
            raise ValueError(
                "expected one or two arguments, got %d instead" % len(args))

    def _init_from_ref(self, ref):
        """Initialize from gist reference,
        which can be an <owner>/<name> string, a gist ID, or a full gist URL.
        """
        if furl(ref).host:
            self._init_from_url(ref)
        elif '/' in ref:
            try:
                owner, name = ref.split('/')
                self._init_from_name(owner, name)
            except ValueError:
                raise GistError("%r is not a valid gist reference; "
                                "try '<owner>/`<name>`" % ref)
        else:
            self._id = ref

    def _init_from_url(self, url):
        """Initialize from gist URL."""
        url = furl(url)
        if url.host != self.GITHUB_GISTS_HOST:
            raise GistError("unrecognized gist URL domains: %s" % url.host)

        self._url = url
        try:
            self._owner, self._id = url.path.segments
        except ValueError:
            raise GistError("invalid format of GitHub gist URL: %s" % url)

    def _init_from_name(self, owner, name):
        """Initialize from gist's owner and name."""
        self._owner = owner
        self._name = name

#: Host part of the GitHub gists' URLs.
GITHUB_GISTS_HOST = 'gist.github.com'


class GistError(ValueError):
    """Exception raised when gist object got invalid arguments."""


class GistCommand(Enum):
    """Command to carry out against the gist."""

    #: Run the gist's code. This should be the default.
    RUN = 'run'

    #: Output the path to gist's binary.
    WHICH = 'which'

    #: Print the complete source code of the gist's binary.
    PRINT = 'print'

    #: Open the gist's HTML page (on GitHub) in the default web browser.
    OPEN = 'open'

    #: Display summary information about the gist.
    INFO = 'info'

    @property
    def long_flag(self):
        return '--' + self.value

    @property
    def short_flag(self):
        return '-' + self.value[0]

    @property
    def flags(self):
        return [self.short_flag, self.long_flag]

    @classmethod
    def for_flag(cls, flag):
        """Return :class:`GistCommand` matching given command line flag."""
        for cmd in cls:
            if flag in (cmd.short_flag, cmd.long_flag):
                return cmd
