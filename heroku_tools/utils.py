# -*- coding: utf-8 -*-
"""Shared utility functions."""
import random
import sys

import click


def prompt_for_pin(prompt, exit_on_failure=True):
    """Prompt user to input random number before continuing.

    This is used for user confirmation prior to taking any
    irreversible action - e.g. a deployment, or data migration.

    Args:
        pre_prompt: a message to print out before the prompt.

    Kwargs:
        exit_on_failure: if True (default) then immediately call sys.exit()
            if the user does not enter the correct PIN; if False, then
            return False to the calling procedure instead.

    """
    random_pin = "%0.6d" % (random.randint(0, 999999))
    if prompt not in (None, ""):
        click.echo(prompt)
    pin = raw_input("Type in the code shown to continue [%s]: " % random_pin)
    if pin == random_pin:
        return True
    else:
        if exit_on_failure:
            click.echo("PIN incorrect.")
            sys.exit(0)
        else:
            return False


def prompt_for_action(question, default):
    """Return confirmation from user for an action.

    Pose a question as a binary yes/no in the standard *nix format:

        Question with a default of True?  [Y/n]:
        Question with a default of False? [y/N]:

    The function returns the True/False outcome, incorporating
    the relevant default value in the case of an empty response.

    Any answer that starts with a 'y' is taken as True.

    """
    if default is True:
        # if the default is True, the a 'y' or nothing is good
        action = raw_input(question + ' [Y/n]: ')
        return action == '' or action.lower().startswith('y')
    else:
        # if the default is False, then only a 'y' will do
        action = raw_input(question + ' [y/N]: ')
        return action.lower().startswith('y')


def split_print_lines(text, delimiter='\n', line_format='  * %s'):
    """Split a block of text and print out as lines."""
    for line in text.lstrip().rstrip().split(delimiter):
        click.echo(line_format % line)
