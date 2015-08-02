"""
Tests for the logic of running gists.
"""
import shlex

from furl import furl
import mock
import requests
from taipan.testing import TestCase

from gisht import BIN_DIR
import gisht.gists.run as __unit__


EXTENSION = '.huh'
INTERPRETER = 'wat'
INTERPRETER_ARGV = INTERPRETER + ' %(script)s -- %(args)s'

OWNER = 'JohnDoe'
NAME = 'foo' + EXTENSION
GIST = '%s/%s' % (OWNER, NAME)

ARGS = ('a', 'bc')


class RunGist(TestCase):
    URL = 'http://example.com/' + GIST
    NOT_A_GIST = 'Alice has a cat'

    @mock.patch.object(__unit__, 'run_gist_url')
    def test_url(self, mock_run_gist_url):
        __unit__.run_gist(self.URL)
        mock_run_gist_url.assert_called_once_with(
            furl(self.URL), (), local=False)

    @mock.patch.object(__unit__, 'run_named_gist')
    def test_name(self, mock_run_named_gist):
        __unit__.run_gist(GIST)
        mock_run_named_gist.assert_called_once_with(GIST, ())

    def test_unknown(self):
        with self.assertRaises(ValueError) as r:
            __unit__.run_gist(self.NOT_A_GIST)

        msg = str(r.exception)
        self.assertIn("unrecognized", msg)
        self.assertIn(self.NOT_A_GIST, msg)


@mock.patch.object(__unit__, 'ensure_gist', new=mock.Mock())
class RunGistUrl(TestCase):
    GIST_ID = '1a2s3d4f5g6h7j8k9l'

    def test_invalid__wrong_host(self):
        gist = furl('http://www.example.com')
        with self.assertRaises(SystemExit):
            __unit__.run_gist_url(gist)

    def test_invalid__malformed_path(self):
        gist = furl('http://' + __unit__.GITHUB_GISTS_HOST + '/foo')
        with self.assertRaises(SystemExit):
            __unit__.run_gist_url(gist)

    @mock.patch.object(__unit__, 'get_gist_info')
    def test_invalid__failed_gist(self, mock_get_gist_info):
        mock_get_gist_info.side_effect = requests.exceptions.HTTPError()

        gist = self._url(OWNER, self.GIST_ID)
        with self.assertRaises(SystemExit):
            __unit__.run_gist_url(gist)

        mock_get_gist_info.assert_called_once_with(self.GIST_ID)

    @mock.patch.object(__unit__, 'run_named_gist')
    @mock.patch.object(__unit__, 'get_gist_info')
    def test_success__no_args(self, mock_get_gist_info, mock_run_named_gist):
        mock_get_gist_info.return_value = {
            'owner': {'login': OWNER},
            'files': {NAME: '__unused__'},
        }

        gist = self._url(OWNER, self.GIST_ID)
        __unit__.run_gist_url(gist)

        mock_run_named_gist.assert_called_once_with(GIST, ())

    @mock.patch.object(__unit__, 'run_named_gist')
    @mock.patch.object(__unit__, 'get_gist_info')
    def test_success__with_args(self, mock_get_gist_info, mock_run_named_gist):
        mock_get_gist_info.return_value = {
            'owner': {'login': OWNER},
            'files': {NAME: '__unused__'},
        }

        gist = self._url(OWNER, self.GIST_ID)
        __unit__.run_gist_url(gist, ARGS)

        mock_run_named_gist.assert_called_once_with(GIST, ARGS)

    # Utility functions

    def _url(self, owner, gist_id):
        return furl('http://%s/%s/%s' % (__unit__.GITHUB_GISTS_HOST,
                                         owner, gist_id))


@mock.patch.dict(__unit__.COMMON_INTERPRETERS, {EXTENSION: INTERPRETER_ARGV})
class RunNamedGist(TestCase):
    EXECUTABLE = BIN_DIR / GIST

    @mock.patch('os.execv')
    def test_direct__no_args(self, mock_execv):
        __unit__.run_named_gist(GIST)

        executable = bytes(self.EXECUTABLE)
        mock_execv.assert_called_once_with(executable, [executable])

    @mock.patch('os.execv')
    def test_direct__with_args(self, mock_execv):
        __unit__.run_named_gist(GIST, ARGS)

        executable = bytes(self.EXECUTABLE)
        mock_execv.assert_called_once_with(
            executable, [executable] + list(ARGS))

    @mock.patch('os.execvp')
    @mock.patch('os.execv')
    def test_via_interpreter__known__no_args(self, mock_execv, mock_execvp):
        mock_execv.side_effect = self._exec_format_error()
        __unit__.run_named_gist(GIST)

        argv = shlex.split(INTERPRETER_ARGV % dict(script=self.EXECUTABLE,
                                                   args=''))
        mock_execvp.assert_called_once_with(INTERPRETER, argv)

    @mock.patch('os.execvp')
    @mock.patch('os.execv')
    def test_via_interpreter__known__with_args(self, mock_execv, mock_execvp):
        mock_execv.side_effect = self._exec_format_error()
        __unit__.run_named_gist(GIST, ARGS)

        argv = shlex.split(INTERPRETER_ARGV % dict(script=self.EXECUTABLE,
                                                   args=' '.join(ARGS)))
        mock_execvp.assert_called_once_with(INTERPRETER, argv)

    @mock.patch('os.execv')
    def test_via_interpreter__unknown(self, mock_execv):
        mock_execv.side_effect = self._exec_format_error()

        gist = GIST.replace(EXTENSION, '.unknown')
        with self.assertRaises(SystemExit):
            __unit__.run_named_gist(gist)

    @mock.patch('os.execv')
    def test_via_interpreter__no_extension(self, mock_execv):
        mock_execv.side_effect = self._exec_format_error()

        gist = GIST.replace(EXTENSION, '')
        with self.assertRaises(SystemExit):
            __unit__.run_named_gist(gist)

    # Utility functions

    def _exec_format_error(self):
        e = OSError()
        e.errno = 8
        return e
