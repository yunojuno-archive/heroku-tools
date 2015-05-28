# -*- coding: utf-8 -*-
"""Package declaration for heroku_tools, inc. main entry point"""
import json

import click

import config
import deploy


@click.group()
def entry_point():
    """Application entry point - a group container for sub-commands."""
    pass


@click.command()
def settings():
    """Print out current settings."""
    click.echo("""
    Settings collated from the following sources:

    * .herokutoolsconf (if exists), overrides
    * environment variables (HEROKU_TOOLS_*), overrides
    * default values

%s
""" % json.dumps(config.settings, indent=4))

# add sub-commands to the main entrypoint
entry_point.add_command(settings)
entry_point.add_command(deploy.deploy_application)
entry_point.add_command(config.configure_application)
