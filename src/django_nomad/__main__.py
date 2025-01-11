import io
import sys

import django

from django_nomad.management.commands.nomad import Command

django.setup()

# Mimic args when the command is called as a django-admin command.
# Required because commands assume positional values in sys.argv.
argv = ["django-admin", "nomad"] + sys.argv[1:]
Command(stdout=io.StringIO(), stderr=io.StringIO()).run_from_argv(argv)
