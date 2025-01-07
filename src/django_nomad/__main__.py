import argparse
from pathlib import Path

import django

from . import commands

django.setup()


def valid_path_for_hooks(path):
    # A validator that ensures the given path is a git repo with hooks,
    # but does not contain a post-checkout script.
    path = Path(path)
    git_path = path / ".git"
    githooks_path = git_path / "hooks"
    post_checkout_file = githooks_path / "post-checkout"
    if not git_path.is_dir():
        raise argparse.ArgumentTypeError(
            f"'{path}' does not appear to contain a git repo."
        )
    elif not githooks_path:
        raise argparse.ArgumentTypeError(
            f"'{path}' does not contain a 'hooks' directory."
        )
    elif post_checkout_file.is_file():
        raise argparse.ArgumentTypeError(
            f"'{path}' already contains a post-checkout hook."
        )
    return path


parser = argparse.ArgumentParser(prog="python -m django_nomad")
subparsers = parser.add_subparsers(required=True)

dump_parser = subparsers.add_parser("dump")
dump_parser.set_defaults(func=commands.dump)

# rollback_parser = subparsers.add_parser("rollback")
# rollback_parser.set_defaults(func=commands.rollback)

install_parser = subparsers.add_parser("install")
install_parser.add_argument("dest", type=valid_path_for_hooks)
install_parser.set_defaults(func=commands.install)
args = parser.parse_args()
args.func(args)
