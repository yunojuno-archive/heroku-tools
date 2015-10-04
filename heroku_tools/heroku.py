# -*- coding: utf-8 -*-
"""Heroku API helper functions."""
from dateutil import parser

import click
import requests
import sarge

from heroku_tools.config import settings

HEROKU_API_URL = 'https://api.heroku.com/apps/%s/releases'
HEROKU_API_TOKEN = settings['heroku_api_token']


class HerokuError(Exception):

    """Error raised when something goes wrong interacting with Heroku."""

    pass


class HerokuRelease():

    """Encapsulates a release as described by the Heroku release API.

    See https://devcenter.heroku.com/articles/platform-api-reference#release
    """

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
        return self._json['app']['name']

    @property
    def commit(self):
        """The hash of the commit deployed in the release."""
        if self.description.startswith('Promote'):
            # "Promote my-app v123 75c70c5"
            return self.description.split(' ')[3]
        elif self.description.startswith('Deploy'):
            # "Deploy 75c70c5"
            return self.description.split(' ')[1]
        else:
            return "invalid"

    @property
    def deployed_at(self):
        """The datetime at which the deployment occurred."""
        return parser.parse(self._json['updated_at'])

    @property
    def description(self):
        """The description supplied by Heroku for the release."""
        return str(self._json['description'])

    @property
    def version(self):
        """The version number (supplied by Heroku) of the release."""
        return self._json['version']

    @property
    def deployed_by(self):
        """The name of the person responsible for the release."""
        return str(self._json['user']['email'])


    @classmethod
    def get_latest_deployment(cls, application):
        """Return the most recent release as HerokuRelease object.

        See https://devcenter.heroku.com/articles/platform-api-reference#release  # noqa
        """
        url = HEROKU_API_URL % application
        auth = requests.auth.HTTPBasicAuth('', HEROKU_API_TOKEN)
        headers = {
            'Accept': 'application/vnd.heroku+json; version=3',
            'Range': 'version;max=10,order=desc'
        }
        try:
            releases = requests.get(url, auth=auth, headers=headers).json()
        except Exception as ex:
            raise HerokuError(u"Error calling Heroku API: %s" % ex)

        for r in releases:
            description = r.get('description', '').split(' ')[0]
            if description in ('Promote', 'Deploy'):
                return HerokuRelease(r)
            else:
                click.echo("Ignoring release: %s" % description)

        raise HerokuError(u"No deployments found in API response.")


def _do_heroku_command(application, command):
    """Run a Heroku CLI command ."""
    cmd = "heroku %s --app %s" % (command, application)
    if _async(cmd) > 0:
        raise HerokuError(u"Error running Heroku command '%s'" % cmd)


def run_command(application, command):
    """Run a command against a Heroku application."""
    return _do_heroku_command(application, "run %s" % command)


def toggle_maintenance(application, maintenance_on):
    """Toggle the Heroku maintenance feature on/off."""
    on_off = "on" if maintenance_on else "off"
    return _do_heroku_command(application, "maintenance:%s" % on_off)


def _async(cmd):
    """Run bash command async."""
    r = sarge.run(cmd, stdout=sarge.Capture(), async=True)
    r.close()
    line = r.stdout.readline()
    while line != '':
        click.echo(line.strip())
        line = r.stdout.readline()
    return r.returncode
