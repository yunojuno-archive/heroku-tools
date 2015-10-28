# -*- coding: utf-8 -*-
"""Deployment scripts."""
import os

import click
import sarge

from heroku_tools import git, heroku, utils
from heroku_tools.config import AppConfiguration
from heroku_tools.settings import SETTINGS


def get_release_note(commits, filename="RELEASE_NOTE"):
    """Invoke git editor to create a new release note.

    Args:
        commits: the output from get_commits - a list of 2-tuples
            containing commit hash and message.
    """
    release_note = '\n'.join(["* %s" % c[1] for c in commits])
    try:
        editor = git.get_editor()
        with open(filename, 'w') as f:
            f.write(release_note)
        sarge.run('%s %s' % (editor, filename))
        with open(filename, 'r') as f:
            release_note = f.read()
        os.remove(filename)
        return release_note
    except Exception:
        click.echo("No editor specified.")
        return release_note


@click.command(name='deploy')
@click.argument('target_environment')
@click.option('-c', '--config-file', help="Specify application configuration file to use")  # noqa
@click.option('-b', '--branch', help="Deploy a specific branch")
@click.option('-f', '--force', is_flag=True, help="Run 'git push' with the '-f' force option")  # noqa
@click.option('-s', '--collectstatic', is_flag=True, help="Run collectstatic command post deployment")  # noqa
def deploy_application(target_environment, config_file, branch, force, collectstatic):
    """Deploy a Heroku application.

    Push code via git, run collectstatic and migrate commands, and wrap
    all of this with the maintenance page to prevent users from using the
    site whilst the deployment is running.

    The user is prompted to confirm various options prior to the
    deployment running, and is then required to enter a random number
    displayed on the screen to invoke the deployment.

    The function encacsulates a fixed workflow that maps git-flow to
    heroku environments, by pushing specific branches to specific remotes:

    """
    # read in and parse configuration
    app = AppConfiguration.load(
        config_file or
        os.path.join(SETTINGS['app_conf_dir'], '%s.conf' % target_environment)
    )
    app_name = app.app_name
    branch = branch or app.default_branch
    cmd_collectstatic = SETTINGS['commands']['collectstatic']
    cmd_migrate = SETTINGS['commands']['migrate']
    # used to work out whether the deployment contains migrations 
    match_migrations = SETTINGS['matches']['migrations']

    # get the contents of the proposed deployment
    release = heroku.HerokuRelease.get_latest_deployment(app_name)
    # will collectstatic run as part of the buildpack - it will never run
    # if this is a pipeline deployment, as that bypasses the buildpack
    run_buildpack = not app.use_pipeline
    collectstatic_enabled = release.collectstatic_enabled()

    remote_hash = release.commit
    local_hash = git.get_branch_head(branch)
    if local_hash == remote_hash:
        click.echo(u"Heroku application is up-to-date, aborting deployment.")
        return

    files = git.get_files(remote_hash, local_hash)
    commits = git.get_commits(remote_hash, local_hash)

    click.echo("")
    click.echo("Comparing %s..%s" % (remote_hash, local_hash))
    click.echo("")
    click.echo("The following files have changed since the last deployment:\n")  # noqa
    click.echo("".join(["  * %s\n" % f for f in files]))
    click.echo("")
    click.echo("The following commits will be included in this deployment:\n")  # noqa
    click.echo("".join(["  [%s] %s\n" % (c[0], c[1]) for c in commits]))

    files_include = (lambda p: p in ''.join(files))
    files_include_migrations = files_include(match_migrations)

    # run migrations post-deployment
    run_migrate = force or utils.prompt_for_action(
        u"Do you want to run migrations?",
        files_include_migrations
    )
    run_collectstatic = collectstatic

    # ============== summarise actions ==========================
    click.echo("")
    click.echo("Summary of deployment options:")  # noqa
    click.echo("")
    click.echo("  ----- Deployment SETTINGS -----------")
    click.echo("")
    click.echo("  Git branch:    %s" % branch)
    click.echo("  Target env:    %s (%s)" % (target_environment, app_name))
    click.echo("  Force push:    %s" % force)
    # run the buildpack as a full deployment
    if run_buildpack is True:
        click.echo("  Run buildpack: True")
        click.echo("  Collectstatic: %s" % collectstatic_enabled)
    # pipeline promotion - buildpack won't run
    if app.use_pipeline is True:
        click.echo("  Pipeline:      True")
        click.echo("  Promote:       %s" % app.upstream_app)
    click.echo("")
    click.echo("  ----- Post-deployment commands ------")
    click.echo("")
    if run_migrate:
        click.echo("  migrate:       %s" % cmd_migrate)
    if collectstatic:
        click.echo("  collectstatic: %s" % cmd_collectstatic)
    if not (run_migrate or run_collectstatic):
        click.echo("  (none specfied)")
    click.echo("")
    # ============== / summarise actions ========================

    # put up the maintenance page if required 
    maintenance = utils.prompt_for_action(
        u"Do you want to put up the maintenance page?",
        run_migrate
    )

    if not utils.prompt_for_pin(""):
        exit(0)

    if maintenance:
        click.echo("Putting up maintenance page")
        heroku.toggle_maintenance(app_name, True)

    if app.use_pipeline:
        click.echo("Promoting upstream app: %s" % app.upstream_app)
        heroku.promote_app(app.upstream_app)
    else:
        click.echo("Pushing to git remote")
        git.push(
            remote=git.get_remote_url(app_name),
            local_branch=branch,
            remote_branch='master',
            force=force
        )

    if run_migrate is True:
        click.echo("Running migrate command")
        heroku.run_command(app_name, cmd_migrate)

    if run_collectstatic is True:
        click.echo("Running staticfiles command")
        heroku.run_command(app_name, cmd_collectstatic)

    if maintenance:
        click.echo("Pulling down maintenance page")
        heroku.toggle_maintenance(app_name, False)

    release = heroku.HerokuRelease.get_latest_deployment(app_name)

    if app.add_tag:
        click.echo("Applying git tag")
        git.apply_tag(
            commit=local_hash,
            tag=release.version,
            message="Deployed to %s by %s" % (
                app_name,
                release.deployed_by
            )
        )

    click.echo(release)
    # if release_note and utils.prompt_for_action(
    #     "Would you like to write a release note? ", True):
    #     release_note = get_release_note(commits)
