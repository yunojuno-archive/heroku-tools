Heroku Tools
============

Opinionated tools for managing Heroku applications, based on the workflow used by YunoJuno, outlined in `this blog post <http://tech.yunojuno.com/deploying-django-apps-to-heroku-3>`_.

.. image:: https://travis-ci.org/yunojuno/heroku-tools.svg?branch=master
    :target: https://travis-ci.org/yunojuno/heroku-tools
.. image:: https://badge.fury.io/py/heroku-tools.svg
    :target: https://badge.fury.io/py/heroku-tools

Background
----------

We (YunoJuno) have been deploying our application to Heroku for the past three years, and we've evolved a set of Fabric scripts to help us with this process. This project is extracted out of that work. It includes CLI applications for deploying apps to Heroku and managing configuration via remote config vars.

It is **opinionated**, and enforces a specific workflow, and can (currently) be used for deploying only Django applications.

Workflow
--------

The workflow that this application supports is based on `gitflow <http://nvie.com/posts/a-successful-git-branching-model/>`_, and works in the following way.

The project has two permanent git branches - ``master`` and ``dev`` (as per gitflow), and three Heroku environments: **live**, **uat** and **dev**.

The dev branch is deployed to the **dev** environment, and is where integration testing is done. Developers working locally on feature branches do their own testing locally, and when they are finished, submit pull requests for merging their branch back into dev. When this is done, dev is pushed.

When a release is due, dev is merged into master, and the master branch is pushed to **uat** and **live** environments. The only difference between these two is that **uat** is not public, and so is used for final testing (e.g. User Acceptance Testing). This may map to "pre-production" or "staging" in other projects.

(Following this model, code is pushed 'up' through the environments from **dev** to **uat** to **live**. At the same time, data is migrated down through the environments from **live** to **uat** to **dev**. The **uat** environment is where the latest code meets the latest data - hence it being used for testing. This project will also contain data migration and anonymisation scripts once ported over.)

Heroku Deployments
------------------

Deploying an application to Heroku is often described as being as simple as a single ``git push``, which is technically correct. That will update your application. However, in most real-world scenarios this is wholly inadequate.

In most cases it looks more like this:

1. See what's in the proposed deployment (``git log``)
2. Turn on the app maintenance page
3. Push up the code
4. Run collectstatic ^^
5. Run data migrations
6. Turn off maintenance page
7. Write a release note
8. Inform others of the deployment

This project encapsulates these steps.

^^ Collectstatic will run automatically as part of the default Herkou Django buildpack, but if you are pushing content to CDN this may not be the desired behaviour, and you may wish to run ``collectstatic`` explicitly post-deployment.

.. code:: shell

    $ heroku-tools deploy dev
    $ heroku-tools deploy dev --branch feature/xxx

Migrations are run automatically if the changeset includes files under "/migrations/".

Deployments
-----------

**UPDATE** This project has been scaled back in ambition - the deploy function is no longer generic, and is specifically written for Django.

This project contains a ``deploy`` command line application that reinforces this workflow. It takes a number of options (run ``deploy --help`` for the full list), but by default it will enforce the workflow described above. A deployment the the dev environment will push the dev branch, uat will push master, etc. It will run a diff against the remote Heroku repo to determine the list of commits (and changed files) that will be pushed, and infer from that whether to run the migrations and collectstatic.

The workflow specifics are configured in application / environment files:

.. code:: YAML

    application:

        # the name of the Heroku application
        name: live_app
        # the default branch to push to this application
        branch: master
        # use the heroku pipeline:promote feature
        pipeline: True
        # the upstream application to promote
        upstream: staging_app
        # add a tag to the commit using the release version from Heroku
        add_tag: False
        # add a tag, and write a release note into the tag message (experimental)
        add_rich_tag: False

    # Heroku application environment settings managed by the conf command
    settings:

        DJANGO_DEBUG: True
        DJANGO_SECRET_KEY: foobar
        DJANGO_SETTINGS_MODULE: my_app.settings
        DATABASE_URL: postgres://postgres:postres@heroku.com/my_app

Configuration
-------------

The ``config`` command line application incorporates our `configuration management process <http://tech.yunojuno.com/managing-multiple-heroku-configurations>`_. It sets application environment variables from the settings block in the ``application.conf`` file. Before applying the settings to the Heroku application it will run a diff against the current value of each setting in the local file. It prints out the diff, so that you can see which settings will be applied, and prompts the user to confirm that the settings should be applied before pushing to Heroku.

Status
------

In development. Please don't use right now.
