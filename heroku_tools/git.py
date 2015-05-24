# -*- coding: utf-8 -*-
import os
import envoy

# location of the website git repo directory
WORK_TREE = os.getenv('WORK_TREE', ".")
GIT_DIR = "%s/.git" % WORK_TREE


def _do_git_cmd(command):
    """
    Run specified git command.

    This function is used to ensure that all git commands are run against
    the correct repository by including the the --git-dir and --work-tree
    options. This is required as we are running the commands outside of
    the target repo directory.

    Args:
        command: the command to run - without the 'git ' prefix, e.g.
            "status", "log --oneline", etc.

    Kwargs:
        capture: if True, then returns the output of the command as a string.

    Returns:
        the output of the command as a string if capture=True, else just
        runs the commands and returns None.
    """
    prefix = "git --git-dir=%s --work-tree=%s " % (GIT_DIR, WORK_TREE)
    r = envoy.run(prefix + command)
    if r.status_code > 0:
        raise Exception(
            u"Error running git command '%s': %s"
            % (command, r.std_err)
        )
    return r.std_out


def get_editor():
    """Return the configured editor value.

    Looks first in git.config, then $EDITOR, $VISUAL

    If no editor is found, returns None.

    """
    editor = (
        envoy.run('git config --get core.editor').std_out or
        os.getenv('EDITOR') or
        os.getenv('VISUAL')
    )
    if editor is None:
        raise Exception(
            "No editor configured in git config, "
            "$EDITOR or $VISUAL."
        )

    return editor


def checkout_branch(branch):
    """ Perform a 'git checkout' on the local repo."""
    _do_git_cmd("checkout %s" % branch)


def push(remote, local_branch, remote_branch="master", force=False):
    """Do a git push of a branch to a remote repo."""
    if force:
        _do_git_cmd("push %s %s:%s -f" % (remote, local_branch, remote_branch))
    else:
        _do_git_cmd("push %s %s:%s" % (remote, local_branch, remote_branch))


def get_branch_name():
    """ Return the current branch name (from GIT_DIR)."""
    return _do_git_cmd("rev-parse --abbrev-ref HEAD")


def get_log(commit_from, commit_to='HEAD'):
    """
    Return the oneline format git history between two commits.

    Args:
        commit_from: the commit hash of the earlier commit.

    Kwargs:
        commit_to: the commit hash of the later commit, defaults to HEAD.

    Returns:
        a list of 2-tuples, each containing the commit hash, and the commit
            message.

    e.g. if the commit log looks like this:

        81a5ea8 Fix for failing tests.
         Refactoring of conversations.

    The return value is:

        [
            ('81a5ea8', 'Fix for failing tests.'),
            ('62d49e9', Refactoring of conversations.)
        ]

    """
    command = "log --oneline --no-merges %s..%s" % (commit_from, commit_to)
    return _do_git_cmd(command)


def get_diff(commit_from, commit_to='HEAD'):
    """
    Return the names of all the files that have changed between two commits.

    Args:
        commit_from: the first commit - can be a commit hash or a tag.

    Kwargs:
        commit_to: the last commit - defaults to 'HEAD'. Can be a commit hash
            or a tag.

    Returns:
        a list of fully qualified filenames.
    """
    command = "diff --name-only %s..%s" % (commit_from, commit_to)
    return _do_git_cmd(command)
    # if len(diff) == 0:
    #     return None
    # else:
    #     return [d for d in diff.split('\n')]


def apply_tag(commit, tag, message):
    """Apply a tag to a given git commit."""
    command = "tag -a %s -m  '%s' %s" % (tag, message, commit)
    _do_git_cmd(command)
