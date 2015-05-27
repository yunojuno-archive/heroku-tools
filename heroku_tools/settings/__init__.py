# -*- coding: utf-8 -*-
"""Package declaration for heroku_tools/settings.

Contains the CLI application settings (as distinct from the Heroku
application settings, which are in the config module.)

The settings themselves are loaded at the end of this module, and
are therefore available by importing settings.settings (I know, but
that's namespacing for you).

>>> from heroku_tools.settings import settings

"""
import os

import click
import yaml

CWD = os.getcwd()

DEFAULT_SETTINGS = {
    'app_conf_dir': CWD,
    'git_work_dir': CWD,
    'commands': {
        'migrate': 'python manage.py migrate',
        'collectstatic': 'python manage.py collectstatic',
    },
    'matches': {
        'migrations': '/migrations/',
        'staticfiles': '/static/',
    }
}

ENVIRON_SETTINGS = {
    'app_conf_dir': os.getenv('HEROKU_TOOLS_CONF_DIR'),
    'git_work_dir': os.getenv('HEROKU_TOOLS_WORK_DIR'),
    'editor': os.getenv('EDITOR') or os.getenv('VISUAL'),
    'heroku_api_token': os.getenv('HEROKU_TOOLS_API_TOKEN'),
    'commands': {
        'migrate': os.getenv('HEROKU_TOOLS_MIGRATE_CMD'),
        'collectstatic': os.getenv('HEROKU_TOOLS_STATIC_CMD'),
    },
    'matches': {
        'migrations': os.getenv('HEROKU_TOOLS_MATCH_MIGRATIONS'),
        'staticfiles': os.getenv('HEROKU_TOOLS_MATCH_STATICFILES'),
    }
}


def get_settings(filename):
    """Load configuration for heroku-tools itself.

    Configuration settings are read in in the following order:

    - local .herokutoolsconf YAML file in current working directory
    - environment variables
    - defaults (set in this function)

    This method is called within this module, making all settings available
    to the rest of the application as heroku_tools.conf.settings.

    """
    settings = {
        'app_conf_dir': (
            ENVIRON_SETTINGS.get('HEROKU_TOOLS_CONF_DIR') or
            DEFAULT_SETTINGS.get('app_conf_dir')
        ),
        'git_work_dir': (
            ENVIRON_SETTINGS.get('HEROKU_TOOLS_WORK_DIR') or
            DEFAULT_SETTINGS.get('git_work_dir')
        ),
        'editor': ENVIRON_SETTINGS.get('editor'),
        'heroku_api_token': ENVIRON_SETTINGS.get('HEROKU_TOOLS_API_TOKEN'),
        'commands': {
            'migrate': (
                ENVIRON_SETTINGS.get('HEROKU_TOOLS_MIGRATE_CMD') or
                DEFAULT_SETTINGS['commands']['migrate']
            ),
            'collectstatic': (
                ENVIRON_SETTINGS.get('HEROKU_TOOLS_STATIC_CMD') or
                DEFAULT_SETTINGS['commands']['collectstatic']
            ),
        },
        'matches': {
            'migrations': (
                ENVIRON_SETTINGS.get('HEROKU_TOOLS_MATCH_MIGRATIONS') or
                DEFAULT_SETTINGS['matches']['migrations']
            ),
            'staticfiles': (
                ENVIRON_SETTINGS.get('HEROKU_TOOLS_MATCH_STATICFILES') or
                DEFAULT_SETTINGS['matches']['staticfiles']
            ),
        }
    }

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
                settings['matches'].update(local.get('matches', {}))
                return settings
        except IOError as ex:
            # if we can't read the file just blast through with the defaults.
            click.echo(".herokutoolsconfig file could not be read: %s" % ex)
            return settings
    else:
        click.echo(u"Config does not exist - %s" % filename)
        click.echo(u"Default settings will be applied.")
        return settings

# the default settings can be overridden by a local '.herokutoolsconf' files
SETTINGS = get_settings(os.path.join(os.getcwd(), '.herokutoolsconf'))
