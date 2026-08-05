"""Load Teamwork's mechanical skill, agent, and reference inventory."""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOPOLOGY_PATH = Path("config/teamwork-topology.json")
HOSTS = ("codex", "cursor", "claude")


class TopologyError(ValueError):
    """Raised when the mechanical topology manifest is malformed."""


def _relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TopologyError(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise TopologyError(f"{label} must stay inside the repository")
    return path.as_posix()


def _unique_names(rows: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        raise TopologyError(f"{label} must be a non-empty list")
    if not all(isinstance(row, dict) for row in rows):
        raise TopologyError(f"{label} entries must be objects")
    names = [row.get("name") for row in rows]
    if any(not isinstance(name, str) or not name for name in names):
        raise TopologyError(f"{label} names must be non-empty strings")
    if len(names) != len(set(names)):
        raise TopologyError(f"{label} names must be unique")
    return rows


def validate_topology(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise TopologyError("topology must be a schema_version 1 object")

    skills = _unique_names(value.get("public_skills"), "public_skills")
    for row in skills:
        name = row["name"]
        if set(row) != {"name", "path"}:
            raise TopologyError(f"public skill {name} must contain only name and path")
        path = _relative_path(row.get("path"), f"public skill {name} path")
        if path != f"skills/{name}/SKILL.md":
            raise TopologyError(f"public skill {name} path does not match its name")

    agents = _unique_names(value.get("agents"), "agents")
    for row in agents:
        name = row["name"]
        if set(row) != {"name", "templates"}:
            raise TopologyError(f"agent {name} must contain only name and templates")
        templates = row.get("templates")
        if not isinstance(templates, dict) or set(templates) != set(HOSTS):
            raise TopologyError(f"agent {name} must declare one template for every host")
        for host, path in templates.items():
            _relative_path(path, f"agent {name} {host} template")

    root_methods = value.get("root_owned_methods")
    if not isinstance(root_methods, list) or not root_methods or not all(
        isinstance(method, str) and method for method in root_methods
    ) or len(root_methods) != len(set(root_methods)):
        raise TopologyError("root_owned_methods must be a unique non-empty string list")

    references = value.get("owned_references")
    if not isinstance(references, list) or not all(isinstance(path, str) for path in references):
        raise TopologyError("owned_references must be a string list")
    normalized_references = [_relative_path(path, "owned reference") for path in references]
    if len(normalized_references) != len(set(normalized_references)):
        raise TopologyError("owned_references must be unique")

    retired = value.get("retired")
    if not isinstance(retired, dict) or set(retired) != {
        "public_skills", "agents", "references", "allowed_path_classes"
    }:
        raise TopologyError("retired inventory is incomplete")
    for key in ("public_skills", "agents"):
        if not isinstance(retired[key], dict):
            raise TopologyError(f"retired.{key} must be an object")
    if set(retired["public_skills"]) & {row["name"] for row in skills}:
        raise TopologyError("a public skill cannot also be retired")
    if set(retired["agents"]) & {row["name"] for row in agents}:
        raise TopologyError("an active agent cannot also be retired")
    if not isinstance(retired["references"], list):
        raise TopologyError("retired.references must be a list")
    for path in retired["references"]:
        _relative_path(path, "retired reference")
    path_classes = retired["allowed_path_classes"]
    if not isinstance(path_classes, dict) or not path_classes:
        raise TopologyError("retired.allowed_path_classes must be a non-empty object")
    for label, prefixes in path_classes.items():
        if not isinstance(label, str) or not isinstance(prefixes, list) or not prefixes:
            raise TopologyError("retired path classes need names and non-empty prefix lists")
        for prefix in prefixes:
            _relative_path(prefix, f"retired path class {label}")
    return value


@lru_cache(maxsize=8)
def load_topology(root: Path = ROOT) -> dict[str, Any]:
    path = root / TOPOLOGY_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TopologyError(f"cannot load {TOPOLOGY_PATH}: {exc}") from exc
    return validate_topology(value)


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


def categorized_retired_path(path: str, root: Path = ROOT) -> str | None:
    classes = load_topology(root)["retired"]["allowed_path_classes"]
    for label, prefixes in classes.items():
        if any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in prefixes):
            return label
    return None


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Query Teamwork's mechanical topology manifest.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("skills")
    subparsers.add_parser("references")
    agents = subparsers.add_parser("agent-templates")
    agents.add_argument("--host", choices=HOSTS, required=True)
    agents.add_argument("--field", choices=("name", "path", "stem"), default="path")
    retired = subparsers.add_parser("retired")
    retired.add_argument("--kind", choices=("public_skills", "agents", "references"), required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "skills":
        for name in sorted(public_skill_paths(root)):
            print(name)
    elif args.command == "references":
        for path in sorted(owned_references(root)):
            print(path)
    elif args.command == "agent-templates":
        for name, path in sorted(host_role_paths(root)[args.host].items()):
            if args.field == "name":
                print(name)
            elif args.field == "stem":
                print(Path(path).stem)
            else:
                print(path)
    else:
        value = load_topology(root)["retired"][args.kind]
        for item in sorted(value if isinstance(value, list) else value):
            print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
