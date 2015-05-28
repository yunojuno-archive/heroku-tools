# -*- coding: utf-8 -*-
import json
import unittest

import mock

from heroku import HerokuRelease


class MockResponse():

    def json(self):
        """Return JSON representation."""
        return json.load(open('test_data/foo.json', 'r'))


def mock_get(*args, **kwargs):
    return MockResponse()


class HerokuReleaseTests(unittest.TestCase):

    @mock.patch('requests.get', mock_get)
    def test_get_latest_deployment(self):

        h = HerokuRelease.get_latest_deployment('x')
        print h