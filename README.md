# django-migrant 

![Branch Status](https://img.shields.io/github/actions/workflow/status/powlo/django-migrant/test.yml?label=master)
![Coverage](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fgist.githubusercontent.com%2Fpowlo%2Fcf4b630256dbda26650c528b9eecede5%2Fraw%2Fdjango-migrant_coverage.json&query=%24.totals.percent_covered_display&suffix=%25&label=coverage)
<!-- ![GitHub Release](https://img.shields.io/github/v/release/powlo/django-migrant) -->
![GitHub License](https://img.shields.io/github/license/powlo/django-migrant)

`django-migrant` is a tool that allows developers to automatically migrate their development database when switching from one git branch to another. A common use case is when asked to run a collegue's branch. With `django-migrant` you no longer need to figure out which migrations need to be rolled back in order to then apply another branch's migrations.

> [!IMPORTANT]
> The tool relies on proper reverse migrations having been written!

## Requirements:

- A django project, version controlled using git, with database migrations.


## How it works.

django-migrant will create a post-checkout hook in a repositories "hooks" directory.

When you checkout a branch the hook will determine which django migrations need to be rolled back, go to the previous branch and roll back, then return to your target branch and migrate forwards.

It will track the changes needed by creating a `.migrant` directory containing a `nodes.json`.


## Installation

1) Install the python package.

        pip install git+https://github.com/powlo/django-migrant@master

2) Install the post-checkout hook:

        python -m django_migrant install <destination> [-i <interpreter>]

    Eg,

        python -m django_migrant install .

    Will attempt to install the hook in the current directory.
    
    The interpreter used by the hook can be configured using the optional `-i` / `--interpreter` switch:

        python -m django_migrant install . -i ./myvenv/bin/python

3) **IMPORTANT!** Read and verify the post-checkout hook and change permissions to allow it to be invoked.

    Eg,

        cd <mydjangoproject>
        chmod +x ./.git/hooks/post-checkout

If you wish you can specify the package as a django app:

    # settings.py
    INSTALLED_APPS = [
        # ...
        "django_migrant",
        # ...
    ]

And then change the invocation to use django admin command.

Eg,

    #!/bin/bash
    # .git/hooks/post-checkout

    # ...
    if [ "$is_branch_checkout" == "1" ]; then
        ./manage.py django_migrant migrate # <--- here
    fi

(But this doesn't change the tool's behaviour.)
