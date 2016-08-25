# -*- coding: utf-8 -*-
"""Package declaration for heroku_tools/settings.

Contains the CLI application settings (as distinct from the Heroku
application settings, which are in the config module.)

The settings themselves are loaded at the end of this module.

>>> from heroku_tools import settings
>>> settings.app_conf_dir
foo/bar
>>>

"""
import os

import click
import sarge
import yaml

CWD = os.getcwd()


def _auth_token():
    """Call the heroku auth:token api.

    This function is inside settings, not Heroku, as it's part of the
    settings process, and is only called once, on startup.

    """
    r = sarge.capture_stdout('heroku auth:token')
    if r.returncode > 0:
        # git doesn't play nicely so r.stderr is None even though it failed
        raise Exception(u"Error getting heroku auth_token")
    return r.stdout.text.strip()


DEFAULT_SETTINGS = {
    'app_conf_dir': CWD,
    'git_work_dir': CWD,
    'commands': {
        'migrate': 'python manage.py migrate',
        'collectstatic': 'python manage.py collectstatic --noinput',
    },
    'heroku_api_token': os.getenv('HEROKU_API_TOKEN'),
}

if DEFAULT_SETTINGS['heroku_api_token'] is None:
    click.echo("No HEROKU_API_TOKEN environment variable set, checking Heroku API.")
    DEFAULT_SETTINGS['heroku_api_token'] = _auth_token()


def get_settings(filename):
    """Load configuration for heroku-tools itself.

    Configuration settings are read in in the following order:

    - local .herokutoolsconf YAML file in current working directory
    - DEFAULT_SETTINGS

    This method is called within this module, making all settings available
    to the rest of the application as heroku_tools.conf.settings.

    """
    settings = DEFAULT_SETTINGS

    if filename in (None, ''):
        click.echo(u"No config specified, default settings will be applied.")
        return settings

    if os.path.exists(filename):
        click.echo(u"Applying settings from %s" % filename)
        try:
            with open(filename, 'r') as settings_file:
                local = yaml.load(settings_file)
                settings.update(local.get('settings', {}))
                settings['commands'].update(local.get('commands', {}))
                return settings
        except IOError as ex:
            # if we can't read the file just blast through with the defaults.
            click.echo(".herokutoolsconf file could not be read: %s" % ex)
            return settings
    else:
        click.echo(u"Config does not exist - %s" % filename)
        click.echo(u"Default settings will be applied.")
        return settings

# the default settings can be overridden by a local '.herokutoolsconf' files
_setttings = get_settings(os.path.join(os.getcwd(), '.herokutoolsconf'))

# provide easy access to the settings
app_conf_dir = _setttings['app_conf_dir']
git_work_dir = _setttings['git_work_dir']
commands = _setttings['commands']
migrate_cmd = commands['migrate']
collectstatic_cmd = commands['collectstatic']
heroku_api_token = _setttings['heroku_api_token']


@click.command(name='settings')
def print_settings():
    """Print out current settings."""
    click.echo(r"-------------------------------------")
    click.echo(r"app_conf_dir      = %s" % app_conf_dir)
    click.echo(r"git_work_dir      = %s" % git_work_dir)
    click.echo(r"migrate_cmd       = %s" % migrate_cmd)
    click.echo(r"collectstatic_cmd = %s" % collectstatic_cmd)
    click.echo(r"heroku_api_token  = %s" % heroku_api_token)
    click.echo(r"-------------------------------------")
