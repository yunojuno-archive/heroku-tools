# -*- coding: utf-8 -*-
"""Configuration for heroku-tools itself and Heroku applications."""
import os

import click
import yaml

from . import (
    heroku,
    settings,
    utils
)


class ConfigurationError(Exception):

    """Exception used when encountering a configuration error."""

    pass


class AppConfiguration(object):

    """Heroku application configuration, with helper methods."""

    def __init__(self, application, settings):
        """Initialise with environments list and commands dict."""
        self.application = application
        self.settings = settings

    @classmethod
    def load(cls, filename):
        """Create new object from file."""
        try:
            with open(filename, 'r') as f:
                config = yaml.load(f)
                app = AppConfiguration(
                    application=config.get('application'),
                    settings=config.get('settings'),
                )
                # if pipeline is set, we need upstream also
                if app.use_pipeline and not app.upstream_app:
                    raise ConfigurationError(
                        u"Invalid configuration - pipeline is set to run, "
                        "but no upstream app is defined."
                    )
                return app
        except IOError:
            raise ConfigurationError(
                u"Unable to read app configuration file: %s" % filename
            )

    @property
    def app_name(self):
        """Name of the Heroku application."""
        return self.application['name']

    @property
    def default_branch(self):
        """Default branch to deploy to application."""
        return self.application['branch']

    @property
    def use_pipeline(self):
        """Deploy using Heroku's pipeline feature."""
        return self.application.get('pipeline', False)

    @property
    def upstream_app(self):
        """App to promote if use_pipeline is True."""
        return self.application.get('upstream', None)

    @property
    def add_tag(self):
        """Add release version as a git tag post-deployment."""
        return self.application.get('add_tag', False)

    @property
    def post_deploy_tasks(self):
        """A list of strings to be executed as shell commands after deployment"""
        return self.application.get('post_deploy', [])


def compare_settings(local_config_vars, remote_config_vars):
    """Compare local and remote settings and return the diff.

    This function takes two dictionaries, and compares the two. Any given
    setting will have one of the following statuses:

    '=' In both, and same value for both (no action required)
    '!' In both, but with different values (an 'update' to a known setting)
    '+' [In local, but not in remote (a 'new' setting to be applied)
    '?' In remote, but not in local (reference only - these are generally
        Heroku add-on specfic settings that do not need to be captured
        locally; they are managed through the Heroku CLI / website.)

    NB This function will convert all local settings values to strings
    before comparing - as the environment settings on Heroku are string.
    This means that, e.g. if a bool setting is 'true' on Heroku and True
    locally, they will **not** match.

    Returns a list of 4-tuples that contains:

        (setting name, local value, remote value, status)

    The status value is one of '=', '!', '+', '?', as described above.

    """
    diff = []
    for k, v in local_config_vars.items():
        if k in remote_config_vars:
            if str(remote_config_vars[k]) == str(v):
                diff.append((k, v, remote_config_vars[k], '='))
            else:
                diff.append((k, v, remote_config_vars[k], '!'))
        else:
            diff.append((k, v, None, '+'))

    # that's the local settings done - now for the remote settings.
    for k, v in remote_config_vars.items():
        if k not in local_config_vars:
            diff.append((k, None, v, '?'))

    return sorted(diff)


def print_diff(diff, statuses=['=', '+', '?', '!']):
    """
    Print out the local:remote settings diff, indicating mismatches.

    This function uses the diff format returned from 'compare_settings',
    which is a list of 4-tuples (key, local setting, remote setting, status).
    Settings are listed in alphabetical order, with a single char prefix
    indicating whether the remote setting needs to be updated or not.

    Kwargs:
        statuses: a list of char status values that will be printed. This
            can be used to filter the print out, so that, for instance, remote-
            only vars are written out separately (recommended).
    """
    key_names = [k[0] for k in diff]
    max_length = len(max(key_names, key=len))
    for key, local, remote, status in diff:
        if status in statuses:
            kmax = key.ljust(max_length)
            if status == '=':  # it's a match
                print u'  %s: %s' % (kmax, local)
            elif status == '+':  # it's a new setting
                print u'+ %s: %s' % (kmax, local)
            elif status == '!':  # it's a mismatch
                print u'! %s: %s (remote = %s)' % (kmax, local, remote)
            elif status == '?':  # it's a remote setting
                print u'? %s: %s (remote only)' % (kmax, remote)
            else:
                print u"Unknown status for %s: %s" % (key, status)


def set_vars(application, settings):
    """Set remote Heroku environment variables.

    Args:
        application: the name of the Heroku application to update.
        settings: a list of 4-tuples as returned from the get_vars function.
            This list will be used to update remote settings to the current
            local value.
    """
    # prompt_for_pin(None)
    # the Heroku config:set command takes a space delimited set of k=v pairs
    cmd_args = " ".join([("%s=%s" % (s[0], s[1])) for s in settings])
    command = u"config:set %s" % cmd_args
    heroku.run_cmd(application, command)


@click.command(name='config')
@click.argument('target_environment')
def configure_application(target_environment):
    r"""Configure Heroku application settings.

    Run a diff between local configuration and remote settings
    and apply any updates to the remote application:

    1. Load local configuration (from target_environment.conf)\n
    2. Fetch remote application config vars (via API)\n
    3. Compare the two\n
    4. Display the diff\n
    5. Prompt user for confirmation to apply updates\n
    6. Apply updates

    """
    app = AppConfiguration.load(
        os.path.join(settings.app_conf_dir, '%s.conf' % target_environment)
    )
    app_name = app.app_name
    release = heroku.HerokuRelease.get_latest_deployment(app_name)
    diff = compare_settings(app.settings, release.get_config_vars())

    print u"\nLocal settings (diff shown by '!', '+' indicator):\n"
    print_diff(diff, statuses=['=', '+', '!'])

    print u"\nRemote-only settings (probably Heroku-specific and ignorable):\n"
    remote_only = [d[0] for d in diff if d[3] == '?']
    print u", ".join(remote_only)

    updates = [d for d in diff if d[3] in ['!', '+']]
    if len(updates) == 0:
        print u"\nAll settings are up-to-date. No action required."
        return

    print u"\nThe following settings will be applied to '%s':\n" % app_name
    for key, local, _, status in updates:
        print u"%s %s=%s" % (status, key, local)
    print u""

    if utils.prompt_for_pin(""):
        set_vars(app_name, updates)
