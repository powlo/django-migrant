# django-migrant 

![Github Branch Status](https://img.shields.io/github/check-runs/powlo/django-migrant/master)
![Coverage](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fgist.githubusercontent.com%2Fpowlo%2Fcf4b630256dbda26650c528b9eecede5%2Fraw%2Fdjango-migrant_coverage.json&query=%24.totals.percent_covered_display&suffix=%25&label=coverage)
![Pypi Version](https://img.shields.io/pypi/v/django-migrant)
![GitHub License](https://img.shields.io/github/license/powlo/django-migrant)

`django-migrant` is a tool that allows developers to automatically migrate their development database when switching from one git branch to another. A common use case is when asked to run a colleague's branch. With `django-migrant` you no longer need to figure out which migrations need to be rolled back in order to then apply another branch's migrations.

> [!IMPORTANT]
> The tool relies on proper reverse migrations having been written!

## Requirements:

- A django project, version controlled using git, with database migrations.


## How it works.

`django-migrant` will create a `post-checkout` and a `pre-rebase` hook in a repository's "hooks" directory.

When you checkout a branch the hook will determine which django migrations need to be rolled back, go to the previous branch and roll back, then return to your target branch and migrate forwards.

The tool deliberately does not perform migration operations during a `git rebase` however, assuming the rebase goes well (🤞), it should just be a case of running `./manage.py migrate`, right? 🙂

## Installation

1) Install the python package.

        pip install django-migrant

2) Add django_migrant to settings.py

        #settings.py
        INSTALLED_APPS = [
            # ...
            "django_migrant",
            # ...
        ]

2) Install the post-checkout hook:

        ./manage.py migrant install <destination>

    Eg,

        ./manage.py migrant install .

    ...will attempt to install the hook in the current directory.

3) Review and adapt the hooks if necessary.

The hooks are installed assuming that the application has been added to settings.py and that the appropriate python interpreter is available when executing the hook. This should work for most users.

However, instead of adding `django_migrant` to your INSTALLED_APPS, you may wish to change the post-checkout script to invoke the python module directly. For example:

    #.git/hooks/post-checkout
    DJANGO_SETTINGS_MODULE=myproject.settings python -m django_migrant migrate

Similarly, you may wish to specify the full path to the python interpreter:

    #.git/hooks/post-checkout
    /home/myname/virtualenvs/myproject/bin/python ./manage.py migrant migrate

Check the hook invocation matches the nuances of your own environment.

**IMPORTANT!** Change the permissions on the hooks to allow them to be invoked.

Eg,

    chmod +x ./.git/hooks/post-checkout
    chmod +x ./.git/hooks/pre-rebase
