import json
from pathlib import Path

from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader
from dulwich import porcelain
from dulwich.repo import Repo


def dump(args):
    base_path = Path(".")
    repo = Repo(".")
    branch = porcelain.active_branch(repo)
    filename = base_path / ".nomad" / "branch" / branch.decode() / "nodes.json"
    connection = connections[DEFAULT_DB_ALIAS]
    loader = MigrationLoader(connection)
    migration_keys = json.dumps(list(loader.disk_migrations.keys()))
    filename.parent.mkdir(exist_ok=True, parents=True)
    with open(filename, "w+") as fh:
        fh.write(migration_keys)


def find_targets(args):
    connection = connections[DEFAULT_DB_ALIAS]
    loader = MigrationLoader(connection)
    base_path = Path(".")

    src_filename = base_path / ".nomad" / "branch" / args.src / "nodes.json"
    with open(src_filename) as fh:
        src_nodes = fh.read()

    dest_filename = base_path / ".nomad" / "branch" / args.dest / "nodes.json"
    with open(dest_filename) as fh:
        dest_nodes = fh.read()

    src_nodes = set([tuple(x) for x in json.loads(src_nodes)])
    dest_nodes = set([tuple(x) for x in json.loads(dest_nodes)])
    node_names = src_nodes - dest_nodes
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
        print(f"{t[0]} {t[1]}")
