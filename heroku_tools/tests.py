# -*- coding: utf-8 -*-
import json
import unittest

import mock

from heroku_tools.heroku import HerokuRelease


class MockResponse(object):
    """Mock requests library response.json()."""
    def json(self):
        """Return JSON representation."""
        return json.load(open('test_data/foo.json', 'r'))


def mock_get(*args, **kwargs):
    return MockResponse()


class HerokuReleaseTests(unittest.TestCase):

    @mock.patch('requests.get', mock_get)
    def test_get_latest_deployment(self):
        """Test unpacking of Heroku API release JSON."""
        release = HerokuRelease.get_latest_deployment('x')
        print release
