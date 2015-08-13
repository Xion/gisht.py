"""
Module defining data types used throughout the application.
"""
from enum import Enum


__all__ = ['GistCommand']


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
