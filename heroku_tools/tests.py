# -*- coding: utf-8 -*-
import json
import unittest

from mock import patch, call

from heroku_tools.heroku import HerokuRelease


class MockResponse(object):
    """Mock requests library response.json()."""
    def json(self):
        """Return JSON representation."""
        return json.load(open('heroku_tools/test_data/foo.json', 'r'))


def mock_get(*args, **kwargs):
    return MockResponse()


class HerokuReleaseTests(unittest.TestCase):

    def setUp(self):
        self.json_input = {'app': {'name': 'hulahoop'}}
        self.herokurelease = HerokuRelease(self.json_input)

    @patch("heroku_tools.heroku.call_api")
    @patch("heroku_tools.heroku.click.echo")
    @patch("heroku_tools.heroku.HerokuRelease")
    def test_get_latest_deployment(self, HerokuRelease, echo, call_api):
        """Test unpacking of Heroku API release JSON."""
        call_api.return_value = [{'description': 'Deploy'},
                                 {'description': 'Promote'}]
        self.herokurelease.get_latest_deployment('x')
        self.assertEqual(HerokuRelease.call_args,
                         call({'description': 'Deploy'}))

        #  If no Deploy or Promote description HerokuError will be raised
        from heroku_tools.heroku import HerokuError
        call_api.return_value = [{'description': 'Hulahoop'}]
        with self.assertRaises(HerokuError):
            self.herokurelease.get_latest_deployment('x')
            print echo.call_args

    @patch("requests.auth.HTTPBasicAuth")
    @patch("requests.get", side_effect=mock_get)
    def test_call_api(self, get, HTTPBasicAuth):

        """Test call_api function of heroku_tools"""

        HTTPBasicAuth.return_value = "authorized"
        from heroku_tools.heroku import call_api
        result = call_api('endpoint-%s', 'application', 'range_header')
        self.assertEqual(get.call_args, call('endpoint-application',
                                             auth='authorized',
                                             headers={'Range': 'range_header',
                                                      'Accept': 'application/vnd.heroku+json; version=3'}))
        self.assertEqual(result, [{u'created_at': u'2013-06-15T15:01:29Z',
                                   u'description': u'Initial release',
                                   u'app': {u'id': u'1b5d48f7-1863-4db4-a108-cc1f7928dacc',
                                            u'name': u'test_app'},
                                   u'updated_at': u'2013-06-15T15:01:29Z', u'slug': None,
                                   u'version': 1, u'user': {u'email': u'hugo@example.com',
                                                            u'id': u'f7ee12b5-4343-4bfc-aae4-195a392d913d'},
                                   u'id': u'c0d15ac3-4101-459d-8c68-ce02a662b068'},
                                  {u'created_at': u'2013-06-18T14:07:52Z', u'description': u'Deploy 99ed2b0',
                                   u'app': {u'id': u'1b5d48f7-1863-4db4-a108-cc1f7928dacc', u'name': u'test_app'},
                                   u'updated_at': u'2013-06-18T14:07:52Z', u'slug':
                                       {u'id': u'c15c01b2-6d41-443b-ba13-bf358fbc7821'}, u'version': 17,
                                   u'user': {u'email': u'hugo@example.com',
                                             u'id': u'f7ee12b5-4343-4bfc-aae4-195a392d913d'},
                                   u'id': u'2fa73c36-4b25-4797-b374-f1f3be994ff2'}])