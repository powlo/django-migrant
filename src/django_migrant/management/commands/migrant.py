import json
import os
import subprocess
import sys
from importlib import resources
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader

MIGRANT_FILENAME = Path(".") / ".migrant"


def stage_one():
    connection = connections[DEFAULT_DB_ALIAS]
    loader = MigrationLoader(connection)
    targets = set(loader.applied_migrations) - set(loader.disk_migrations)

    targets_as_json = json.dumps(list(targets))
    with open(MIGRANT_FILENAME, "w+") as fh:
        fh.write(targets_as_json)

    env_with_stage_two = os.environ.copy()
    env_with_stage_two["DJANGO_MIGRANT_STAGE"] = "TWO"
    # NB: We use raw subprocess because dulwich (used to interface with git repos)
    # doesn't support the relative branch "-".
    subprocess.run(["git", "checkout", "-", "--quiet"], env=env_with_stage_two)


def stage_two():
    connection = connections[DEFAULT_DB_ALIAS]
    loader = MigrationLoader(connection)
    with open(MIGRANT_FILENAME) as fh:
        node_names = [tuple(n) for n in json.loads(fh.read())]

    nodes = [loader.graph.node_map[n] for n in node_names]

    targets = set()
    for n in nodes:
        if not n.parents:
            targets.add((n.key[0], "zero"))
        else:
            for parent in n.parents:
                if parent not in nodes:
                    targets.add(parent.key)
    for t in list(targets):
        call_command("migrate", t[0], t[1])

    env_with_stage_three = os.environ.copy()
    env_with_stage_three["DJANGO_MIGRANT_STAGE"] = "THREE"
    subprocess.run(["git", "checkout", "-", "--quiet"], env=env_with_stage_three)


def stage_three():
    call_command("migrate")


class Command(BaseCommand):
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(
            title="sub-commands",
            required=True,
        )

        install_parser = subparsers.add_parser(
            "install",
            help="Installs the command to run in a 'post-checkout' git hook.",
        )
        install_parser.set_defaults(method=self.install)
        install_parser.add_argument("dest")
        install_parser.add_argument("-i", "--interpreter", default=sys.executable)

        migrate_parser = subparsers.add_parser(
            "migrate",
            help="Migrates database seemlessly from one git branch to another.",
        )

        migrate_parser.set_defaults(method=self.migrate)

    def handle(self, *args, method, **options):
        method(*args, **options)

    def install(self, *args, **options):
        path = Path(options["dest"])
        git_path = path / ".git"

        # Validate the given destination.
        if not git_path.is_dir():
            raise CommandError(f"'{path}' does not appear to contain a git repo.")

        dest_git_hooks_path = git_path / "hooks"
        if not dest_git_hooks_path:
            raise CommandError(f"'{path}' does not contain a 'hooks' directory.")

        self.create_hook(dest_git_hooks_path, "post-checkout")
        self.create_hook(dest_git_hooks_path, "pre-rebase")

    def create_hook(self, path: Path, name: str):
        hook_filename = path / name
        if hook_filename.is_file():
            ok_to_append = input(
                f"'{name}' hook already exists. Append to file [y/N]? "
            )
            if ok_to_append.upper() != "Y":
                raise CommandError(f"'{path}' already contains a post-checkout hook.")
            exists = True
        else:
            exists = False

        template_filename = resources.files("django_migrant") / "hook_templates" / name

        with open(template_filename, "r") as fh:
            content = fh.read()

        if not exists:
            header_filename = (
                resources.files("django_migrant") / "hook_templates" / "header"
            )
            with open(header_filename, "r") as fh:
                header = fh.read()

            header = header.replace("{{ name }}", str(name))
        else:
            header = ""

        content = header + content
        with open(hook_filename, "a") as fh:
            fh.write(content)

        self.stdout.write(f"{name} hook created: {hook_filename}")

    def migrate(self, *args, **options):
        DJANGO_MIGRANT_STAGE = os.environ.get("DJANGO_MIGRANT_STAGE")
        if not DJANGO_MIGRANT_STAGE:
            stage_one()
        elif DJANGO_MIGRANT_STAGE == "TWO":
            stage_two()
        elif DJANGO_MIGRANT_STAGE == "THREE":
            stage_three()
