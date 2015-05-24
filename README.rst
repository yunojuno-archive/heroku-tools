Heroku Tools
============

Opinionated tools for managing Heroku applications, based on the workflow used by YunoJuno, outlined in [this blog post](http://tech.yunojuno.com/deploying-django-apps-to-heroku-3).

Background
----------

We (YunoJuno) have been deploying our application to Heroku for the past three years, and we've evolved a set of Fabric scripts to help us with this process. This project is extracted out of that work. It includes CLI applications for deploying apps to Heroku, managing configuration of apps (via env vars), and migrating data between apps.

It is **opinionated**, and enforces a specific workflow.

Workflow
--------

The workflow that this application supports is based on [gitflow](http://nvie.com/posts/a-successful-git-branching-model/), and works in the following way.

The project has two permanent git branches - ``master`` and ``dev`` (as per gitflow), and three Heroku environments: **live**, **uat** and **dev**.

The dev branch is deployed to the dev environment, and is where integration testing is done. Developers working locally on feature branches do their own testing locally, and when they are finished, submit pull requests for merging their branch back into dev. When this is done, dev is pushed.

When a release is due, dev is merged into master, and the master branch is pushed to uat and live environments. The only difference between these two is that uat is not public, and so is used for final testing (e.g. User Acceptance Testing). This may map to "pre-production" or "staging" in other projects.

(Following this model, code is pushed 'up' through the environments from dev to uat to live. At the same time, data is migrated down through the environments from live to uat to dev. The uat environment is where the latest code meets the latest data - hence it being used for testing. This project will also contain data migration and anonymisation scripts once ported over.)

Heroku Deployments
------------------

Deploying an application to Heroku is often described as being as simple as a single ``git push``, which is technically correct. That will update your application. However, in most real-world scenarios this is wholly inadequate.

In most cases it looks more like this:

1. See what's in the proposed deployment (``git log``)
2. Turn on the maintenance page (esp. if it contains data migrations)
3. Push up the code (``git push``)
4. Run any data migrations required by the deployment
5. Run ``collectstatic`` (or equivalent) if static content has changed
6. Turn off maintenance page
7. Write a release note
8. Inform others of the deployment

This project encapsulates all of the above.

..code::shell

    $ deploy dev
    $ deploy dev --branch feature/xxx

Migrations are run automatically if the changeset includes files under "/migrations/", and collectstatic is run if the changeset includes "/static/".

Deployments
-----------

This project contains a ``deploy`` command line application that reinforces this workflow. It takes a number of options (run ``deploy --help`` for the full list), but by default it will enforce the workflow described above. A deployment the the dev environment will push the dev branch, uat will push master, etc. It will run a diff against the remote Heroku repo to determine the list of commits (and changed files) that will be pushed, and infer from that whether to run the migrations and collectstatic.

The workflow specifics are configured in a YAML file:

..code::YAML

    environments:

        - label:    live
          app_name: mapp_app_1
          branch:   master

        - label:    uat
          app_name: my_app_2
          branch:   master

        - label:    dev
          app_name: my_app_3
          branch:   dev

    commands:

        collectstatic: python manage.py collectstatic
        migrate: python manage.py migrate

Configuration
-------------

TBC - but this will incorporate our [configuration management process](http://tech.yunojuno.com/managing-multiple-heroku-configurations).

Data
----

TBC - this will include our data migration and anonymisation process.