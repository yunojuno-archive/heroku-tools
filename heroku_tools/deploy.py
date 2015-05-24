# -*- coding: utf-8 -*-
"""Deployment scripts."""
import os
import random
import sys

import click
import envoy
import yaml

import git
import heroku

# # Config file can be supplied, but need a default, which is in the same dir
DEFAULT_CONFIG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'deploy.yaml'
)


class Configuration():

    """Encapsulate deployment configuration, with helper methods."""

    def __init__(self, environments, commands):
        """Initialise with environments list and commands dict."""
        self.environments = environments
        self.commands = commands

    @classmethod
    def load(cls, filename):
        """Create new object from file."""
        with open(filename, 'r') as f:
            config = yaml.load(f)
        return Configuration(
            environments=config['environments'],
            commands=config['commands']
        )

    def get_command(self, command):
        """Return command from the configuration."""
        return self.commands[command]

    def get_environment(self, environment):
        """Return a single environment config as a dict."""
        return [e for e in self.environments if e['label'] == environment][0]

    def get_environment_setting(self, environment, setting, default=None):
        """Return a single environment setting."""
        return self.get_environment(environment).get(setting, default)


def prompt_for_pin(prompt, exit_on_failure=True):
    """Prompt user to input random number before continuing.

    Args:
        pre_prompt: a message to print out before the prompt.

    Kwargs:
        exit_on_failure: if True (default) then immediately call sys.exit()
            if the user does not enter the correct PIN; if False, then
            return False to the calling procedure instead.

    """
    p = str(random.randint(0, 10 ** 6 - 1))
    if prompt is not None:
        click.echo(prompt)
    pin = raw_input(
        "Please confirm your intention to continue by typing in '%s' "
        "at the prompt: " % p
    )
    if pin == p:
        return True
    else:
        if exit_on_failure:
            print("PIN incorrect.")
            sys.exit(0)
        else:
            return False


def get_release_note(changelog, filename="RELEASE_NOTE"):
    """Invoke git editor to create a new release note."""
    editor = git.get_editor()
    if editor == '':
        print "No editor specified."
        return changelog
    else:
        with open(filename, 'w') as f:
            f.write(changelog)
        envoy.run('%s %s' % (editor, filename))
        with open(filename, 'r') as f:
            release_note = f.read()
        os.remove(filename)
        return release_note


def get_remote_commit_hash(application):
    """Get commit hash of Heroku application."""
    return str(heroku.get_latest_release(application)[1])


def get_local_commit_hash(branch):
    """Get the hash of the latest commit on a given branch."""
    return git._do_git_cmd("rev-parse %s" % branch)[:7]


def prompt_for_action(question, default):
    """Return confirmation from user for an action."""
    if default is True:
        # if the default is True, the a 'y' or nothing is good
        action = raw_input(question+' [Y/n]: ')
        return action == '' or action.lower().startswith('y')
    else:
        # if the default is False, then only a 'y' will do
        action = raw_input(question+' [y/N]: ')
        return action.lower().startswith('y')


def split_print_lines(text, line_format='  * %s'):
    """Split a block of text and print out as lines."""
    for line in text.lstrip().rstrip().split('\n'):
        click.echo(line_format % line)


@click.command()
@click.argument('target')
@click.option('-f', '--force', is_flag=True, help="Run 'git push' with the '-f' force option")  # noqa
@click.option('-s', '--collectstatic', is_flag=True, help="Run collectstatic command post deployment")  # noqa
@click.option('-m', '--migrate', is_flag=True, help="Run the migrate command post deployment")  # noqa
@click.option('-b', '--branch', help="Deploy a specific branch")
@click.option('-v', '--verbose', is_flag=True, help="Show verbose output")
def deploy(target, force, collectstatic, migrate, branch, verbose):
    """Deploy app to target environment.

    Deploy a Heroku application and run post-deployment commands.

    Push code via git, run collectstatic and migrate commands, and wrap
    all of this with the maintenance page to prevent users from using the
    site whilst the deployment is running.

    The user is prompted to confirm various options prior to the
    deployment running, and is then required to enter a random number
    displayed on the screen to invoke the deployment.

    The function encacsulates a fixed workflow that maps git-flow to
    heroku environments, by pushing specific branches to specific remotes:

    """
    # return
    config = Configuration.load(DEFAULT_CONFIG)
    app_name = config.get_environment_setting(target, 'app_name')
    branch = branch or config.get_environment_setting(target, 'branch')
    cmd_collectstatic = config.get_command('collectstatic')
    cmd_migrate = config.get_command('migrate')

    remote_hash = get_remote_commit_hash(app_name)
    local_hash = get_local_commit_hash(branch)
    diff = git.get_diff(remote_hash, local_hash)
    log = git.get_log(remote_hash, local_hash)

    if verbose:
        click.echo("")
        click.echo("The following files have changed since the last deployment:\n")  # noqa
        split_print_lines(diff)
        click.echo("")
        click.echo("The following commits will be included in this deployment:\n")  # noqa
        split_print_lines(log)
        click.echo("")

    run_migrations = prompt_for_action(
        u"Do you want to run migrations?",
        ('/migrations/' in diff)
    )

    run_collectstatic = collectstatic or prompt_for_action(
        u"Do you want to run collectstatic?",
        ('/static/' in diff)
    )

    # summarise details
    click.echo("")
    click.echo("-------------------------------------")
    click.echo("Git branch:    %s" % branch)
    click.echo("Target env:    %s (%s)" % (target, app_name))
    click.echo("Force push:    %s" % force)
    # click.echo("Pipeline:            %s" % pipeline)
    # click.echo("Notify HipChat:      {hipchat}")
    click.echo("")
    click.echo("Post-deployment commands")
    click.echo("")
    click.echo("Data migrations: %s" % run_migrations)
    click.echo("Collect static:  %s" % run_collectstatic)
    click.echo("-------------------------------------")

    # release_note = get_release_note(log)

    # toggle_maintenance(True)

    # push_to_remote(force=force)

    # if run_migrate is True:
    #     migrate()

    # toggle_maintenance(False)

    # if run_collectstatic is True:
    #     collectstatic()

@click.command()
@click.argument('target')
def config(target):
    """Update Heroku app environment settings."""
    pass

@click.command()
@click.argument('target')
def migrate(target):
    """Migrate data between Heroku applications.

    The TARGET is the label used in the configuration for the
    application into which you wish to migrate data. The source
    application is defined in the configuration also.

    """
    pass


