# -*- coding: utf-8 -*-
"""Configuration for heroku-tools itself and Heroku applications."""
import os

import click
import yaml


def get_settings(filename):
    """Load configuration for heroku-tools itself.

    Configuration settings are read in in the following order:

    - local .herokutoolsconf YAML file in current working directory
    - environment variables
    - defaults (set in this function)

    This method is called within this module, making all settings available
    to the rest of the application as heroku_tools.conf.settings.

    """
    cwd = os.getcwd()
    default_values = {
        'app_conf_dir': os.getenv('HEROKU_TOOLS_CONF_DIR') or cwd,
        'git_work_dir': os.getenv('HEROKU_TOOLS_WORK_DIR') or cwd,
        'editor': os.getenv('EDITOR') or os.getenv('VISUAL'),
        'heroku_api_token': os.getenv('HEROKU_TOOLS_API_TOKEN'),
        'commands': {
            'migrate': (
                os.getenv('HEROKU_TOOLS_MIGRATE_CMD')
                or 'python manage.py migrate'
            ),
            'collectstatic': (
                os.getenv('HEROKU_TOOLS_STATIC_CMD')
                or 'python manage.py collectstatic'
            ),
        },
        'matches': {
            'migrations': (
                os.getenv('HEROKU_TOOLS_MATCH_MIGRATIONS')
                or '/migrations/'
            ),
            'staticfiles': (
                os.getenv('HEROKU_TOOLS_MATCH_STATICFILES')
                or '/static/'
            ),
        }
    }

    if filename in (None, ''):
        click.echo(u"No config specified, default settings will be applied.")
        return default_values

    if os.path.exists(filename):
        click.echo(u"Applying settings from %s" % filename)
    else:
        click.echo(u"Config does not exist - %s" % filename)
        click.echo(u"Default settings will be applied.")
        return default_values

    try:
        with open(filename, 'r') as f:
            local = yaml.load(f)
            settings = default_values.copy()
            settings.update(local.get('settings', {}))
            settings['commands'].update(local.get('commands', {}))
            settings['matches'].update(local.get('matches', {}))
            return settings
    except IOError as ex:
        # if we can't read the file just blast through with the defaults.
        click.echo(".herokutoolsconfig file could not be read: %s" % ex)
        return default_values


class ConfigurationError(Exception):

    """Exception used when encountering a configuration error."""

    pass


class AppConfiguration():

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

    def add_tag(self):
        """Add release version as a git tag post-deployment."""
        return self.application.get('add_tag', False)


@click.command(name='config')
@click.argument('target_environment')
def configure_application(target_environment):
    """Configure Heroku application settings.

    Run a diff between the remote Heroku application settings and a local
    settings file, print out the results, and push the difference to Heroku.

    """
    pass

# the default settings can be overridden by a local '.herokutoolsconf' files
settings = get_settings(os.path.join(os.getcwd(), '.herokutoolsconf'))
