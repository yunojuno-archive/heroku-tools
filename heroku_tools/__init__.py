# -*- coding: utf-8 -*-
"""Package declaration for heroku_tools, inc. main entry point"""
import click

from deploy import deploy


@click.group()
def entry_point():
    """Application entry point - a group container for sub-commands."""
    pass

# add sub-commands to the main entrypoint
entry_point.add_command(deploy.deploy)
