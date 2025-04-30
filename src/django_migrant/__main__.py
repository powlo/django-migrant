import sys

import django

from django_migrant.management.commands.migrant import Command

django.setup()

# Mimic args when the command is called as a django-admin command.
# Required because commands assume positional values in sys.argv.
argv = ["django-admin", "migrant"] + sys.argv[1:]
Command().run_from_argv(argv)
