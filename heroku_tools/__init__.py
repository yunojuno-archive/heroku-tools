# -*- coding: utf-8 -*-
"""Package declaration for heroku_tools, inc. main entry point"""
import click

from . import (
    config,
    settings,
    deploy
)


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

# add sub-commands to the main entrypoint
entry_point.add_command(settings.init_app_conf)
entry_point.add_command(settings.print_settings)
entry_point.add_command(deploy.deploy_application)
entry_point.add_command(config.configure_application)
