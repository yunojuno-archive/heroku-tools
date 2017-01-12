# -*- coding: utf-8 -*-
import json
import unittest
from mock import patch, call

from . import utils
from .heroku import HerokuRelease, HerokuError
from .git import get_commits


class MockResponse(object):
    """Mock requests library response.json()."""
    def json(self):
        """Return JSON representation."""
        return json.load(open('heroku_tools/test_data/foo.json', 'r'))

    @property
    def status_code(self):
        return 200


def mock_get(*args, **kwargs):
    return MockResponse()


class HerokuReleaseTests(unittest.TestCase):

    def setUp(self):
        json_data = json.load(open('heroku_tools/test_data/foo.json', 'r'))
        self.json_input = json_data[1]
        self.initial_release_json = json_data[0]
        self.herokurelease = HerokuRelease(self.json_input)

    @patch("heroku_tools.heroku.call_api")
    @patch("heroku_tools.heroku.click.echo")
    @patch("heroku_tools.heroku.HerokuRelease")
    def test_get_latest_deployment(self, HerokuRelease, echo, call_api):
        """Test unpacking of Heroku API release JSON."""
        call_api.return_value = [
            {'description': 'Deploy'},
            {'description': 'Promote'}
        ]
        self.herokurelease.get_latest_deployment('x')
        call_api.assert_called_once_with(
            'https://api.heroku.com/apps/%s/releases',
            'x',
            range_header='version;max=10,order=desc'
        )
        HerokuRelease.assert_called_once_with({'description': 'Deploy'})

        #  If no Deploy or Promote description HerokuError will be raised
        # from heroku_tools.heroku import HerokuError
        call_api.return_value = [{'description': 'Hulahoop'}]
        with self.assertRaises(HerokuError):
            self.herokurelease.get_latest_deployment('x')

        # now test with the HEROKU_API_MAX_RELEASE set
        call_api.return_value = [{'description': 'Deploy'}]
        with patch('heroku_tools.heroku.HEROKU_API_MAX_RANGE', 1):
            self.herokurelease.get_latest_deployment('x')
            call_api.assert_called_with(
                'https://api.heroku.com/apps/%s/releases',
                'x',
                range_header='version;max=1,order=desc'
            )

    @patch("requests.auth.HTTPBasicAuth")
    @patch("requests.get", side_effect=mock_get)
    def test_call_api(self, get, HTTPBasicAuth):

        """Test call_api function of heroku_tools"""

        HTTPBasicAuth.return_value = "authorized"
        from heroku_tools.heroku import call_api
        result = call_api('endpoint-%s', 'application', 'range_header')
        self.assertEqual(
            get.call_args,
            call(
                'endpoint-application',
                auth='authorized',
                headers={
                    'Range': 'range_header',
                    'Accept': 'application/vnd.heroku+json; version=3'
                }
            )
        )
        self.assertEqual(
            result,
            [{
                u'created_at': u'2013-06-15T15:01:29Z',
                u'description': u'Initial release',
                u'app': {
                    u'id': u'1b5d48f7-1863-4db4-a108-cc1f7928dacc',
                    u'name': u'test_app'
                },
                u'updated_at': u'2013-06-15T15:01:29Z',
                u'slug': None,
                u'version': 1,
                u'user':
                    {
                        u'email': u'hugo@example.com',
                        u'id': u'f7ee12b5-4343-4bfc-aae4-195a392d913d'
                    },
                u'id': u'c0d15ac3-4101-459d-8c68-ce02a662b068'
            }, {
                u'created_at': u'2013-06-18T14:07:52Z', u'description': u'Deploy 99ed2b0',
                u'app': {
                    u'id': u'1b5d48f7-1863-4db4-a108-cc1f7928dacc',
                    u'name': u'test_app'
                },
                u'updated_at': u'2013-06-18T14:07:52Z',
                u'slug': {
                    u'id': u'c15c01b2-6d41-443b-ba13-bf358fbc7821'
                },
                u'version': 17,
                u'user': {
                    u'email': u'hugo@example.com',
                    u'id': u'f7ee12b5-4343-4bfc-aae4-195a392d913d'
                },
                u'id': u'2fa73c36-4b25-4797-b374-f1f3be994ff2'
            }]
        )

    @patch("heroku_tools.heroku.parser")
    def test_heroku_attributes(self, parser):
        for attribute in ('version', 'description'):
            self.assertEqual(
                getattr(self.herokurelease, attribute),
                self.json_input[attribute]
            )
        self.assertEqual(
            self.herokurelease.deployed_by,
            self.json_input['user']['email']
        )
        parser.parse.return_value = '2013-06-18T14:07:52Z'
        self.assertEqual(
            self.json_input['updated_at'],
            self.herokurelease.deployed_at
        )

    def test_commit(self):

        """Test for getting commit hash from description"""

        result = self.herokurelease.commit
        self.assertEqual(self.json_input['description'].split(' ')[1], result)
        initial_release = HerokuRelease(self.initial_release_json)
        self.assertEqual(initial_release.commit, 'invalid')
        deploy_json = self.json_input
        deploy_json["description"] = "Promote my-app v123 75c70c5"
        deploy = HerokuRelease(deploy_json)
        self.assertEqual(deploy.commit, '75c70c5')


class UtilsTests(unittest.TestCase):

    def setUp(self):
        self.raw_input_patcher = patch("heroku_tools.utils.raw_input")
        self.mock_raw_input = self.raw_input_patcher.start()
        self.click_echo_patcher = patch("heroku_tools.utils.click.echo")
        self.mock_click_echo = self.click_echo_patcher.start()

    def tearDown(self):
        self.mock_raw_input.stop()
        self.mock_click_echo.stop()

    @patch("heroku_tools.utils.sys.exit")
    @patch("heroku_tools.utils.random.randint")
    def test_prompt_for_pin(self, mock_randint, mock_sys_exit):

        # Wrong pin

        self.mock_raw_input.return_value = 99999
        mock_randint.return_value = 66666
        pin = utils.prompt_for_pin(None, exit_on_failure=False)
        self.assertFalse(mock_sys_exit.called)
        self.assertFalse(pin)
        pin = utils.prompt_for_pin(None, exit_on_failure=True)
        self.assertTrue(mock_sys_exit.called)
        self.assertEqual(mock_sys_exit.call_args, call(0))
        self.assertEqual(self.mock_click_echo.call_args, call('PIN incorrect.'))
        self.assertFalse(pin)

        # Right pin

        self.mock_raw_input.return_value = str(999999)
        mock_randint.return_value = 999999
        pin = utils.prompt_for_pin(None, exit_on_failure=True)
        self.assertTrue(pin)
        pin_with_prompt = utils.prompt_for_pin("This is a prompt",
                                               exit_on_failure=True)
        self.assertEqual(self.mock_click_echo.call_args, call('This is a prompt'))
        self.assertTrue(pin_with_prompt)

    def test_prompt_for_action(self):
        self.mock_raw_input.return_value = ''
        answer = utils.prompt_for_action("Do you like hulahoop ?", True)
        self.assertTrue(answer)
        self.assertEqual(self.mock_raw_input.call_args,
                         call('Do you like hulahoop ? [Y/n]: '))
        answer_default_false = utils.prompt_for_action("Do you like hulahoop ?", False)
        self.assertFalse(answer_default_false)

    def test_split_print_lines(self):
        input_text = "line1, line2, line3"
        utils.split_print_lines(input_text, delimiter=",")
        self.assertEqual(
            self.mock_click_echo.call_args_list,
            [
                call('  * line1'),
                call('  *  line2'),
                call('  *  line3')
            ]
        )


class GitTests(unittest.TestCase):

    """Tests for the git module functions."""

    @patch('heroku_tools.git.run_git_cmd')
    def test_get_commits(self, mock_git):
        """Test the parsing of one-line git commit logs."""
        # check that it works with variables commit hash lengths (git
        # defaults to 7 chars, but may increase this based on the
        # likelihood of a clash.
        mock_git.return_value = (
            "81a5ea8 Fix failing tests\n"
            "62d49e9ab Refactor foobar"
        )
        commits = get_commits('ABC', 'DEF')
        mock_git.assert_called_once_with('log --oneline --no-merges ABC..DEF')
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0], ['81a5ea8', 'Fix failing tests'])
        self.assertEqual(commits[1], ['62d49e9ab', 'Refactor foobar'])
