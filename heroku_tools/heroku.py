# -*- coding: utf-8 -*-
"""Heroku API bits and bobs."""
import os
import requests

# HEROKU_API_KEY = envoy.run("heroku auth:token", capture=True).std_out.rstrip()
HEROKU_API_KEY = os.getenv('HEROKU_API_TOKEN')
HEROKU_API_URL = 'https://api.heroku.com/apps/%s/releases'


def get_releases(application):
    """
    Get application release log from Heroku.

    Args:
        application: the name of the application on Heroku.

    Returns:
        JSON - see https://devcenter.heroku.com/articles/platform-api-reference#release
    """
    url = HEROKU_API_URL % application
    auth = requests.auth.HTTPBasicAuth('', HEROKU_API_KEY)
    return requests.get(url, auth=auth).json()


def get_latest_release(application):
    """
    Get the commit hash, version number of the latest release to Heroku.

    Args:
        application: the name of the application on Heroku.

    Returns:
        A 5-tuple containing:
            the version,
            commit hash,
            release description,
            user,
            date,
            e.g. (u'v31', u'7a0e825', u'Deployed', u'hugo', u'2013/07/11 04:46:37 -0700')
    """
    releases = get_releases(application)
    latest = releases[-1]
    return (
        latest["name"],
        latest["commit"],
        latest['descr'],
        latest['user'],
        latest['created_at']
    )
