"""Semantic boundaries and manifest-driven topology checks."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping

from teamwork_tooling.topology import (
    TopologyError,
    agent_template_paths,
    categorized_retired_path,
    host_role_paths,
    load_topology,
    owned_references,
    public_skill_paths,
)

from .contracts import EvalError, ROOT


FORBIDDEN_ACTIVE_CONCEPTS = {
    "teamwork-collaborate": (
        ("numbered L1/L2/L3 runtime states", (r"\bL[123]\b",)),
        ("fixed child cap", (r"(?:daily cap|cap4|five to eight|5[-–]8|total children)",)),
    ),
    "teamwork-plan": (
        ("durable Collaborate gate", (r"(?:accepted|durable).{0,80}Collaborate.{0,80}(?:gate|readback|required)",)),
    ),
    "teamwork-review": (
        ("mandatory repair ceremony", (r"one repair batch|mandatory.{0,80}recheck",)),
    ),
    "teamwork-goal": (
        ("per-round transaction ledger", (r"(?:each|every|per).{0,60}(?:round|turn).{0,80}(?:transaction|ledger|write)",)),
    ),
    "teamwork-init": (
        (
            "Init-owned migration mechanics",
            (
                r"(?:have|ask|give)\s+Worker.{0,120}(?:migrat|convert|old[- ]format reader|compatibility shim|dual[- ](?:read|write))",
                r"(?:Init|this Skill)\s+(?:owns?|performs?|runs?|executes?).{0,100}(?:migrat|convert)",
            ),
        ),
        (
            "old-format runtime compatibility",
            (
                r"(?:Init|this Skill|current runtime)\s+(?:supports?|reads?|runs?|maintains?|installs?|adds?|provides?).{0,100}(?:old|legacy|pre[- ]?7|compatibility|dual[- ](?:read|write))",
            ),
        ),
    ),
}


def normalize_semantic_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def discover_skill_inventory(root: Path = ROOT) -> dict[str, Path]:
    skill_root = root / "skills"
    if not skill_root.is_dir():
        raise EvalError("skills/ is missing")
    inventory: dict[str, Path] = {}
    for directory in sorted(path for path in skill_root.iterdir() if path.is_dir()):
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            raise EvalError(f"skills/{directory.name}: top-level skill directory lacks SKILL.md")
        inventory[directory.name] = skill_file
    return inventory


def parse_frontmatter(source: str, path: str) -> tuple[str, str]:
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", source, re.DOTALL)
    if not match:
        raise EvalError(f"{path}: missing YAML frontmatter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise EvalError(f"{path}: malformed frontmatter line: {line}")
        key, value = line.split(":", 1)
        if key in fields:
            raise EvalError(f"{path}: duplicate frontmatter key: {key}")
        fields[key] = value.strip()
    if set(fields) != {"name", "description"}:
        raise EvalError(f"{path}: frontmatter must contain only name and description")
    if not fields["description"].startswith("Use when "):
        raise EvalError(f"{path}: description must start with 'Use when '")
    return fields["name"], fields["description"]


def validate_skill_source_contract(skill: str, source_text: str) -> None:
    path = f"skills/{skill}/SKILL.md"
    name, _description = parse_frontmatter(source_text, path)
    if name != skill:
        raise EvalError(f"{path}: frontmatter name must match directory")
    for label, patterns in FORBIDDEN_ACTIVE_CONCEPTS.get(skill, ()):
        if any(re.search(pattern, source_text, re.IGNORECASE | re.DOTALL) for pattern in patterns):
            raise EvalError(f"{path}: retired behavioral concept remains: {label}")


def validate_collaboration_layers_reference_contract(source_text: str) -> None:
    raise EvalError("collaboration-layers.md is retired and has no active contract")


def dependency_cycles(edges: Mapping[str, Iterable[str]]) -> list[list[str]]:
    visiting: list[str] = []
    active: set[str] = set()
    visited: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if node in active:
            cycles.append(visiting[visiting.index(node):] + [node])
            return
        if node in visited:
            return
        active.add(node)
        visiting.append(node)
        for target in edges.get(node, ()):
            visit(target)
        visiting.pop()
        active.remove(node)
        visited.add(node)

    for node in sorted(edges):
        visit(node)
    return cycles


def validate_skill_topology(root: Path = ROOT) -> dict[str, object]:
    try:
        manifest_skills = public_skill_paths(root)
        manifest_references = set(owned_references(root))
        retired = load_topology(root)["retired"]
    except TopologyError as exc:
        raise EvalError(str(exc)) from exc
    inventory = discover_skill_inventory(root)
    names = set(inventory)
    expected_names = set(manifest_skills)
    if names != expected_names:
        raise EvalError(
            "skills/: inventory differs from topology manifest; "
            f"missing={sorted(expected_names - names)}, extra={sorted(names - expected_names)}"
        )
    retired_names = names & set(retired["public_skills"])
    if retired_names:
        raise EvalError(f"skills/: retired public skill remains active: {sorted(retired_names)}")

    behavior_refs = {
        path.relative_to(root).as_posix()
        for path in (root / "skills").glob("*/references/**/*")
        if path.is_file()
    }
    if behavior_refs != manifest_references:
        raise EvalError(
            "skills/: reference inventory differs from topology manifest; "
            f"missing={sorted(manifest_references - behavior_refs)}, "
            f"extra={sorted(behavior_refs - manifest_references)}"
        )
    retired_references = set(retired["references"])
    if behavior_refs & retired_references:
        raise EvalError(f"skills/: retired reference remains active: {sorted(behavior_refs & retired_references)}")

    local_scripts = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "skills").glob("*/scripts/**/*")
        if path.is_file()
    )
    if local_scripts:
        raise EvalError(f"skills/: behavioral scripts are not allowed: {local_scripts}")

    edges: dict[str, set[str]] = defaultdict(set)
    cross_loads: list[str] = []
    path_re = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")
    for owner, path in inventory.items():
        source = path.read_text(encoding="utf-8")
        parse_frontmatter(source, manifest_skills[owner])
        for target in path_re.findall(source):
            edges[owner].add(target)
            if target != owner:
                cross_loads.append(f"{owner}->{target}")
    if cross_loads:
        raise EvalError("skills/: cross-skill behavior load is forbidden: " + ", ".join(sorted(cross_loads)))
    cycles = dependency_cycles(edges)
    if cycles:
        raise EvalError("skills/: skill dependency cycle: " + " ; ".join(" -> ".join(c) for c in cycles))
    return {
        "skills": sorted(names),
        "behavior_references": sorted(behavior_refs),
        "cross_skill_loads": cross_loads,
        "cycles": cycles,
    }


def validate_role_template_sources(root: Path = ROOT) -> None:
    mappings = host_role_paths(root)
    roles = set(agent_template_paths(root))
    retired_roles = set(load_topology(root)["retired"]["agents"])
    for host, mapping in mappings.items():
        if set(mapping) != roles:
            raise EvalError(f"templates/{host}-agents/: manifest role mapping is incomplete")
        directory = root / f"templates/{host}-agents"
        observed = {path.relative_to(root).as_posix() for path in directory.iterdir() if path.is_file()}
        expected = set(mapping.values())
        if observed != expected:
            raise EvalError(
                f"templates/{host}-agents/: inventory differs from topology manifest; "
                f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
            )
        for role, source_path in mapping.items():
            source = (root / source_path).read_text(encoding="utf-8")
            normalized = normalize_semantic_text(source).replace("_", "-")
            declared = f'name = "teamwork-{role}"' if host == "codex" else f"name: {role}"
            if declared not in normalized:
                raise EvalError(f"{source_path}: role identity does not match {role}")
            if any(re.search(rf"\b{re.escape(retired)}\b", normalized) for retired in retired_roles):
                raise EvalError(f"{source_path}: retired role identity remains active")


def validate_retired_surface_placement(root: Path = ROOT) -> dict[str, list[str]]:
    """Check retired names on active surfaces while allowing categorized compatibility owners."""

    topology = load_topology(root)
    retired_tokens = [
        *(name for name in topology["retired"]["public_skills"] if name != "teamwork"),
        *topology["retired"]["agents"],
    ]
    active_paths = [
        *public_skill_paths(root).values(),
        *(path for mapping in host_role_paths(root).values() for path in mapping.values()),
        "scripts/install/policy.sh",
        "README.md", "README.en.md", "CODEX.md", "CURSOR.md", "CLAUDE.md", "docs/architecture.md",
    ]
    violations: list[str] = []
    for relative in active_paths:
        path = root / relative
        if not path.is_file():
            continue
        normalized = path.read_text(encoding="utf-8").casefold()
        for token in retired_tokens:
            if re.search(rf"(?<![a-z0-9-]){re.escape(token.casefold())}(?![a-z0-9-])", normalized):
                violations.append(f"{relative}:{token}")
    if violations:
        raise EvalError("retired surface appears in active behavior/docs: " + ", ".join(sorted(violations)))
    return {label: list(prefixes) for label, prefixes in topology["retired"]["allowed_path_classes"].items()}


def validate_retired_reference(path: str, root: Path = ROOT) -> str:
    category = categorized_retired_path(path, root)
    if category is None:
        raise EvalError(f"retired name usage is outside a categorized compatibility owner: {path}")
    return category


def validate_semantic_sources(root: Path = ROOT) -> None:
    topology = validate_skill_topology(root)
    for skill in topology["skills"]:
        path = root / public_skill_paths(root)[skill]
        validate_skill_source_contract(skill, path.read_text(encoding="utf-8"))
    validate_role_template_sources(root)
    validate_retired_surface_placement(root)
