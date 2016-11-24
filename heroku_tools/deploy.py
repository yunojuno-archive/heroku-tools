# -*- coding: utf-8 -*-
"""Deployment scripts."""
import os
import subprocess

import click
import sarge

from . import (
    config,
    git,
    heroku,
    settings,
    utils
)


def run_post_deployment_tasks(tasks):
    # runs post-deployment tasks -- expects them to specify the heroku app involved as required
    for task in tasks:
        subprocess.call(task.split())  # ie, needs to be separated into individual words
    click.echo("Post-deployment tasks completed")


@click.command(name='deploy')
@click.argument('target_environment')
@click.option('-c', '--config-file', help="Specify application configuration file to use")  # noqa
@click.option('-b', '--branch', help="Deploy a specific branch")
@click.option('-f', '--force', is_flag=True, help="Run 'git push' with the '-f' force option")  # noqa
def deploy_application(target_environment, config_file, branch, force):  # noqa
    """Deploy a Heroku application.

    Push code via git, run collectstatic if relevant, then run any specific
    post-deployment commands specced in the configuration file, and wrap
    all of this with the maintenance page to prevent users from using the
    site whilst the deployment is running.

    The user is prompted to confirm various options prior to the
    deployment running, and is then required to enter a random number
    displayed on the screen to invoke the deployment.

    The function encacsulates a fixed workflow that maps git-flow to
    heroku environments, by pushing specific branches to specific remotes:

    """
    # read in and parse configuration
    app = config.AppConfiguration.load(
        config_file or
        os.path.join(settings.app_conf_dir, '%s.conf' % target_environment)
    )
    app_name = app.app_name
    branch = branch or app.default_branch

    # get the contents of the proposed deployment
    release = heroku.HerokuRelease.get_latest_deployment(app_name)

    remote_hash = release.commit
    if app.use_pipeline:
        # if we are using pipelines, then the commit we need is not the
        # local one, but the latest version on the upstream app, as this
        # is the one that will be deployed.
        upstream_release = heroku.HerokuRelease.get_latest_deployment(app.upstream_app)  # noqa
        local_hash = upstream_release.commit
    else:
        local_hash = git.get_branch_head(branch)

    if local_hash == remote_hash:
        click.echo(u"Heroku application is up-to-date, aborting deployment.")
        return

    files = git.get_files(remote_hash, local_hash)
    commits = git.get_commits(remote_hash, local_hash)

    post_deploy_tasks = app.post_deploy_tasks

    click.echo("")
    click.echo("Comparing %s..%s" % (remote_hash, local_hash))
    click.echo("")
    click.echo("The following files have changed since the last deployment:\n")  # noqa
    if len(files) == 0:
        click.echo("  (no change)")
    else:
        click.echo("".join(["  * %s\n" % f for f in files]))
    click.echo("")
    click.echo("The following commits will be included in this deployment:\n")  # noqa
    if len(commits) == 0:
        click.echo("  (no change)")
    else:
        click.echo("".join(["  [%s] %s\n" % (c[0], c[1]) for c in commits]))

    # ============== summarise actions ==========================
    click.echo("")
    click.echo("Summary of deployment options:")  # noqa
    click.echo("")
    click.echo("  ----- Deployment SETTINGS -----------")
    click.echo("")
    click.echo("  Git branch:    %s" % branch)
    click.echo("  Target env:    %s (%s)" % (target_environment, app_name))
    click.echo("  Force push:    %s" % force)
    # pipeline promotion - buildpack won't run
    click.echo("  Pipeline:      %s" % app.use_pipeline)
    if app.use_pipeline:
        click.echo("  Promote:       %s" % app.upstream_app)
    click.echo("  Release tag:   %s" % app.add_tag)
    click.echo("")
    click.echo("  ----- Post-deployment commands ------")
    click.echo("")

    if not post_deploy_tasks:
        click.echo("  (None specified)")
    else:
        [click.echo("  %s" % x) for x in post_deploy_tasks]

    click.echo("")
    # ============== / summarise actions ========================

    # put up the maintenance page if required
    maintenance = utils.prompt_for_action(
        u"Do you want to put up the maintenance page?",
        False
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

    if post_deploy_tasks:
        click.echo("Running post-deployment tasks:")
        run_post_deployment_tasks(post_deploy_tasks)

    if maintenance:
        click.echo("Pulling down maintenance page")
        heroku.toggle_maintenance(app_name, False)

    release = heroku.HerokuRelease.get_latest_deployment(app_name)

    if app.add_tag:
        click.echo("Applying git tag")
        message = "Deployed to %s by %s" % (app_name, release.deployed_by)
        git.apply_tag(commit=local_hash, tag=release.version, message=message)

    click.echo(release)
