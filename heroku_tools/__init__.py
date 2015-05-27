# -*- coding: utf-8 -*-
"""Package declaration for heroku_tools, inc. main entry point"""
import json

import click

from heroku_tools import config, settings, deploy


@click.group()
def entry_point():
    """Command line tools for managing Heroku applications.

    Heroku Tools is an application created out of tools that
    YunoJuno built to manage their Heroku application environments.
    It is opinionated, and enforces a specific configuration of
    environments. This configuration is explained in more detail
    on the YunoJuno tech blog.

    """
    pass


@click.command(name='settings')
def print_settings():
    """Print out current settings."""
    click.echo("""
    Settings collated from the following sources:

    * .herokutoolsconf (if exists), which overrides
    * environment variables (HEROKU_TOOLS_*), which override
    * default values

---
%s
---
    """ % (json.dumps(settings.SETTINGS, indent=4))
    )

# add sub-commands to the main entrypoint
entry_point.add_command(print_settings)
entry_point.add_command(deploy.deploy_application)
entry_point.add_command(config.configure_application)
