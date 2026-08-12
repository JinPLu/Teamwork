"""Load Teamwork's small mechanical Skill and agent inventory."""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOSTS = ("codex", "cursor", "claude")


@lru_cache(maxsize=8)
def load_topology(root: Path = ROOT) -> dict[str, object]:
    value = json.loads((root / "config/teamwork-topology.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Teamwork topology must be a JSON object")
    if set(value) != {"public_skills", "agents", "root_owned_methods", "owned_references"}:
        raise ValueError("Teamwork topology has unexpected fields")
    return value


def public_skill_paths(root: Path = ROOT) -> dict[str, str]:
    return {row["name"]: row["path"] for row in load_topology(root)["public_skills"]}


def agent_template_paths(root: Path = ROOT) -> dict[str, dict[str, str]]:
    return {row["name"]: dict(row["templates"]) for row in load_topology(root)["agents"]}


def host_role_paths(root: Path = ROOT) -> dict[str, dict[str, str]]:
    result = {host: {} for host in HOSTS}
    for role, templates in agent_template_paths(root).items():
        for host, path in templates.items():
            result[host][role] = path
    return result


def owned_references(root: Path = ROOT) -> tuple[str, ...]:
    return tuple(load_topology(root)["owned_references"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("skills")
    sub.add_parser("references")
    agents = sub.add_parser("agent-templates")
    agents.add_argument("--host", choices=HOSTS, required=True)
    agents.add_argument("--field", choices=("name", "path", "stem"), default="path")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "skills":
        for name in sorted(public_skill_paths(root)):
            print(name)
    elif args.command == "references":
        for path in sorted(owned_references(root)):
            print(path)
    else:
        for name, path in sorted(host_role_paths(root)[args.host].items()):
            print(name if args.field == "name" else Path(path).stem if args.field == "stem" else path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
