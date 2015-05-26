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

# add sub-commands to the main entrypoint
entry_point.add_command(deploy.deploy)

@entry_point.command()
def settings():
    """Print out current settings."""
    click.echo("""
    Settings collated from the following sources:

    * .herokutoolsconf (if exists), overrides
    * environment variables (HEROKU_TOOLS_*), overrides
    * default values

%s
""" % json.dumps(config.settings, indent=4))
