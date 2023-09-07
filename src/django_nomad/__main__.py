import argparse

import django

from . import commands

django.setup()
parser = argparse.ArgumentParser(prog="python -m django_nomad")
subparsers = parser.add_subparsers(required=True)

dump_parser = subparsers.add_parser("dump")
dump_parser.set_defaults(func=commands.dump)

find_targets_parser = subparsers.add_parser("find_targets")
find_targets_parser.add_argument("--src", type=str, nargs="?", required=True)
find_targets_parser.add_argument("--dest", type=str, nargs="?", required=True)
find_targets_parser.set_defaults(func=commands.find_targets)

args = parser.parse_args()
args.func(args)
