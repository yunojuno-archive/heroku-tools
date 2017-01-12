# -*- coding: utf-8 -*-
"""Git related commands.

Git module uses the Envoy library to run git commands
against a git repo as configured in settings.SETTINGS
with the WORK_DIR and GIT_DIR values.

"""
import os

import sarge

from . import settings

# location of the website git repo directory
WORK_DIR = settings.git_work_dir
GIT_DIR = os.path.join(WORK_DIR, '.git')
GIT_CMD_PREFIX = "git --git-dir=%s --work-tree=%s " % (GIT_DIR, WORK_DIR)


def run_git_cmd(command):
    """Run specified git command.

    This function is used to ensure that all git commands are run against
    the correct repository by including the the --git-dir and --work-tree
    options. This is required as we are running the commands outside of
    the target repo directory.

    Args:
        command: the command to run - without the 'git ' prefix, e.g.
            "status", "log --oneline", etc.

    Returns the output of the command as a string.

    """
    cmd = GIT_CMD_PREFIX + command
    r = sarge.capture_stdout(cmd)
    if r.returncode > 0:
        # git doesn't play nicely so r.stderr is None even though it failed
        raise Exception(u"Error running git command '%s'" % cmd)
    return r.stdout.text


def get_remote_url(app_name):
    """Return the git remote address on Heroku."""
    return "git@heroku.com:%s.git" % app_name


def push(remote, local_branch, remote_branch="master", force=False):
    """Push a branch to a remote repo."""
    if force:
        run_git_cmd("push %s %s:%s -f" % (remote, local_branch, remote_branch))
    else:
        run_git_cmd("push %s %s:%s" % (remote, local_branch, remote_branch))


def get_current_branch():
    """Return the current branch name (from GIT_DIR)."""
    return run_git_cmd("rev-parse --abbrev-ref HEAD")


def get_branch_head(branch):
    """Return the hash of the latest commit on a given branch."""
    # cast to str as passing unicode to git commands causes them to fail
    return run_git_cmd("rev-parse %s" % branch)[:7]


def get_commits(commit_from, commit_to):
    """Return the oneline format history between two commits.

    Args:
        commit_from: the commit hash of the earlier commit.
        commit_to: the commit hash of the later commit, defaults to HEAD.

    Returns a list of 2-tuples, each containing the commit hash, and the commit
    message.

    e.g. if the commit log looks like this:

        81a5ea8 Fix for failing tests.
        62d49e9 Refactoring of conversations.

    The return value is:

        [
            ('81a5ea8', 'Fix for failing tests.'),
            ('62d49e9', Refactoring of conversations.)
        ]

    """
    command = "log --oneline --no-merges %s..%s" % (commit_from, commit_to)
    raw = run_git_cmd(command)
    lines = raw.lstrip().rstrip().split('\n')
    # split on the first space - separating commit hash and message
    return [l.split(' ', 1) for l in lines if l != '']


def get_files(commit_from, commit_to):
    """Return the names of the files that have changed between two commits.

    Args:
        commit_from: the first commit - can be a commit hash or a tag.
        commit_to: the last commit - can be a commit hash or a tag.

    Returns a list of fully qualified filenames.

    """
    command = "diff --name-only %s..%s" % (commit_from, commit_to)
    raw = run_git_cmd(command)
    files = raw.lstrip().rstrip().split('\n')
    files.sort()
    # strip empty strings
    return [f for f in files if f != '']


def apply_tag(commit, tag, message=None):
    """Apply an annotated tag to a given git commit.

    Args:
        commit: string, the hash of the commit to tag
        tag: string, the tag label

    Kwargs:
        message: string, if supplied then used as the tag message; if
            None, then rely on local git configuration to pop up an
            editor. Commonly used to provide a release note.

    """
    if message is None:
        command = "tag -a %s %s" % (tag, commit)
    else:
        command = "tag -a %s -m  '%s' %s" % (tag, message, commit)
    run_git_cmd(command)
