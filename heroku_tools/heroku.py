# -*- coding: utf-8 -*-
"""Heroku API helper functions."""
from dateutil import parser
import envoy
import requests

from heroku_tools.config import settings

HEROKU_API_URL = 'https://api.heroku.com/apps/%s/releases'
HEROKU_API_TOKEN = settings['heroku_api_token']


class HerokuError(Exception):

    """Error raised when something goes wrong interacting with Heroku."""

    pass


class HerokuRelease():

    """Encapsulates a release as described by the Heroku release API."""

    def __init__(self, raw):
        """Initialise new object from raw JSON as return from API."""
        self._json = raw

    def __unicode__(self):
        return (
            u"Release %s [%s] of %s, deployed by %s at %s" %
            (
                self.version,
                self.commit,
                self.application,
                self.deployed_by,
                self.deployed_at
            )
        )

    def __str__(self):
        return unicode(self).encode('utf-8')

    @property
    def application(self):
        """The name of the application."""
        return self._json['app_name']

    @property
    def commit(self):
        """The hash of the commit deployed in the release."""
        # return as string as unicode kills git commands
        return str(self._json['commit'])

    @property
    def deployed_at(self):
        """The datetime at which the deployment occurred."""
        return parser.parse(self._json['created_at'])

    @property
    def description(self):
        """The description supplied by Heroku for the release."""
        # return as string as unicode kills git commands
        return str(self._json['descr'])

    @property
    def version(self):
        """The version number (supplied by Heroku) of the release."""
        # return as string as unicode kills git commands
        return str(self._json['name'])

    @property
    def deployed_by(self):
        """The name of the person responsible for the release."""
        # return as string as unicode kills git commands
        return str(self._json['user'])

    @classmethod
    def get_latest(cls, application):
        """Return the most recent release as HerokuRelease object.

        See https://devcenter.heroku.com/articles/platform-api-reference#release  # noqa
        """
        url = HEROKU_API_URL % application
        auth = requests.auth.HTTPBasicAuth('', HEROKU_API_TOKEN)
        try:
            raw = requests.get(url, auth=auth).json()[-1]
            raw['app_name'] = application
            return HerokuRelease(raw)
        except Exception as ex:
            raise HerokuError(u"Error calling Heroku API: %s" % ex)


def _do_heroku_command(application, command):
    cmd = "heroku %s --app %s" % (command, application)
    r = envoy.run(cmd)
    if r.status_code > 0:
        raise HerokuError(
            u"Error running Heroku command '%s': %s"
            % (cmd, r.std_err)
        )
    return r.std_out


def run_command(application, command):
    """Run a command against a Heroku application."""
    return _do_heroku_command(application, "run %s" % command)


def toggle_maintenance(application, maintenance_on):
    """Toggle the Heroku maintenance feature on/off."""
    on_off = "on" if maintenance_on else "off"
    return _do_heroku_command(application, "maintenance:%s" % on_off)
