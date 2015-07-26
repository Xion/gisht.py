"""
Tests for the logic of running gists.
"""
import shlex

import mock
from taipan.testing import TestCase

from gisht import BIN_DIR
import gisht.gists.run as __unit__


EXTENSION = '.huh'
INTERPRETER = 'wat'
INTERPRETER_ARGV = INTERPRETER + ' %(script)s -- %(args)s'

GIST = 'JohnDoe/foo' + EXTENSION


@mock.patch.dict(__unit__.COMMON_INTERPRETERS, {EXTENSION: INTERPRETER_ARGV})
class RunGist(TestCase):
    EXECUTABLE = BIN_DIR / GIST
    ARGS = ('a', 'bc')

    @mock.patch('os.execv')
    def test_direct__no_args(self, mock_execv):
        __unit__.run_gist(GIST)

        executable = bytes(self.EXECUTABLE)
        mock_execv.assert_called_once_with(executable, [executable])

    @mock.patch('os.execv')
    def test_direct__with_args(self, mock_execv):
        __unit__.run_gist(GIST, self.ARGS)

        executable = bytes(self.EXECUTABLE)
        mock_execv.assert_called_once_with(
            executable, [executable] + list(self.ARGS))

    @mock.patch('os.execvp')
    @mock.patch('os.execv')
    def test_via_interpreter__known__no_args(self, mock_execv, mock_execvp):
        mock_execv.side_effect = self._exec_format_error()
        __unit__.run_gist(GIST)

        argv = shlex.split(INTERPRETER_ARGV % dict(script=self.EXECUTABLE,
                                                   args=''))
        mock_execvp.assert_called_once_with(INTERPRETER, argv)

    @mock.patch('os.execvp')
    @mock.patch('os.execv')
    def test_via_interpreter__known__with_args(self, mock_execv, mock_execvp):
        mock_execv.side_effect = self._exec_format_error()
        __unit__.run_gist(GIST, self.ARGS)

        argv = shlex.split(INTERPRETER_ARGV % dict(script=self.EXECUTABLE,
                                                   args=' '.join(self.ARGS)))
        mock_execvp.assert_called_once_with(INTERPRETER, argv)

    @mock.patch('os.execv')
    def test_via_interpreter__unknown(self, mock_execv):
        mock_execv.side_effect = self._exec_format_error()

        gist = GIST.replace(EXTENSION, '.unknown')
        with self.assertRaises(SystemExit):
            __unit__.run_gist(gist)

    @mock.patch('os.execv')
    def test_via_interpreter__no_extension(self, mock_execv):
        mock_execv.side_effect = self._exec_format_error()

        gist = GIST.replace(EXTENSION, '')
        with self.assertRaises(SystemExit):
            __unit__.run_gist(gist)

    # Utility functions

    def _exec_format_error(self):
        e = OSError()
        e.errno = 8
        return e
