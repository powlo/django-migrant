# django-nomad 

![Workflow Status](https://img.shields.io/github/actions/workflow/status/powlo/django-nomad/test.yml?label=master)
![GitHub Release](https://img.shields.io/github/v/release/powlo/django-nomad)
![GitHub License](https://img.shields.io/github/license/powlo/django-nomad)

`django-nomad` is a tool that allows developers to automatically migrate their development database when switching from one git branch to another. A common use case is when asked to run a collegues branch you have to figure out which of your migrations need to be rolled back in order to then apply your collegues migrations.

This is especially convenient when your database is populated in a prefered state for your own in-progress development.

But note: The tool relies on proper reverse migrations having been written!

## Requirements:

- A django project, version controlled using git, with database migrations.


## How it works.

django-nomad will create a post-checkout hook in a repositories "hooks" directory.

When you checkout a branch the hook will determine which django migrations need to be rolled back, go to the previous branch and roll back, then return to your target branch and migrate forwards.

It will track the changes needed by creating a `.nomad` directory containing a `nodes.json`. 


## Installation

1) Install the python package.

        pip install git+https://github.com/powlo/django-nomad@master

2) Install the post-checkout hook:

        python -m django_nomad install <destination> [-i <interpreter>]

    Eg,

        python -m django_nomad install .

    Will attempt to install the hook in the current directory.
    
    The interpreter used by the hook can be configured using the optional `-i` / `--interpreter` switch:

        python -m django_nomad install . -i ./myvenv/bin/python

3) **IMPORTANT!** Read and verify the post-checkout hook and change permissions to allow it to be invoked.

    Eg,

        cd <mydjangoproject>
        chmod +x ./.git/hooks/post-checkout

If you wish you can specify the package as a django app:

    # settings.py
    INSTALLED_APPS = [
        # ...
        "django_nomad",
        # ...
    ]

And then change the invocation to use django admin command.

Eg,

    #!/bin/bash
    # .git/hooks/post-checkout

    # ...
    if [ "$is_branch_checkout" == "1" ]; then
        ./manage.py django_nomad migrate # <--- here
    fi

(But this doesn't change the tool's behaviour.)

## Development

    pip install -e git+https://github.com/powlo/django-nomad@master