import json
import os
import shutil
import subprocess
from importlib import resources
from pathlib import Path

from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader

from . import hook_templates


def stage_one():
    base_path = Path(".")
    filename = base_path / ".nomad" / "nodes.json"
    connection = connections[DEFAULT_DB_ALIAS]
    loader = MigrationLoader(connection)
    targets = set(loader.applied_migrations) - set(loader.disk_migrations)

    targets_as_json = json.dumps(list(targets))
    filename.parent.mkdir(exist_ok=True, parents=True)
    with open(filename, "w+") as fh:
        fh.write(targets_as_json)

    env_with_stage_two = os.environ.copy()
    env_with_stage_two["DJANGO_NOMAD_STAGE"] = "TWO"
    subprocess.run(["git", "checkout", "-"], env=env_with_stage_two)


def stage_two():
    connection = connections[DEFAULT_DB_ALIAS]
    loader = MigrationLoader(connection)
    base_path = Path(".")
    src_filename = base_path / ".nomad" / "nodes.json"
    with open(src_filename) as fh:
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
    env_with_stage_three["DJANGO_NOMAD_STAGE"] = "THREE"
    subprocess.run(["git", "checkout", "-"], env=env_with_stage_three)


def stage_three():
    call_command("migrate")


def dump(args):
    DJANGO_NOMAD_STAGE = os.environ.get("DJANGO_NOMAD_STAGE")
    if not DJANGO_NOMAD_STAGE:
        stage_one()
    elif DJANGO_NOMAD_STAGE == "TWO":
        stage_two()
    elif DJANGO_NOMAD_STAGE == "THREE":
        stage_three()


def install(args):
    git_hooks_path = args.dest / ".git" / "hooks"
    post_checkout_file = resources.files(hook_templates) / "post-checkout"

    shutil.copy(post_checkout_file, git_hooks_path)
    print(f"git hook created: {post_checkout_file}")
