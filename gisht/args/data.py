"""
Module defining data types used in command line parsing.
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

    #: Open thr gist's HTML page (on GitHub) in the default web browser.
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
