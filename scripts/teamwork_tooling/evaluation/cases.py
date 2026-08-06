"""Validate change-scoped semantic routing scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from teamwork_tooling.topology import agent_template_paths, public_skill_paths

from .contracts import EvalError, PLATFORMS, ROOT, ROUTING_MANIFEST, SEMANTIC_NAME_RE, SPLITS
from .sources import validate_semantic_sources


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvalError(f"{display_path(path)}: invalid JSON: {exc}") from exc


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{label} must be non-empty text")
    return value


def _owner_paths() -> set[str]:
    return {
        "policy/teamwork-global.md",
        *public_skill_paths(ROOT).values(),
        *(path for mapping in agent_template_paths(ROOT).values() for path in mapping.values()),
    }


def validate_routing_manifest(path: Path = ROUTING_MANIFEST) -> list[dict[str, Any]]:
    value = load_json(path)
    if not isinstance(value, dict) or set(value) != {"schema_version", "platforms", "scenarios"}:
        raise EvalError(f"{display_path(path)}: invalid routing manifest shape")
    if value.get("schema_version") != 2:
        raise EvalError(f"{display_path(path)}: schema_version must be 2")
    platforms = value.get("platforms")
    if not isinstance(platforms, list) or set(platforms) != PLATFORMS:
        raise EvalError("routing scenarios must cover Codex, Cursor, and Claude")
    rows = value.get("scenarios")
    if not isinstance(rows, list) or not rows:
        raise EvalError("routing scenarios must not be empty")
    owners = _owner_paths()
    routes = {"native", *public_skill_paths(ROOT)}
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        required = {"name", "split", "owner", "prompt", "expected_route"}
        if not isinstance(row, dict) or set(row) != required:
            raise EvalError("routing scenario has an invalid shape")
        name = _text(row.get("name"), "routing scenario name")
        if not SEMANTIC_NAME_RE.fullmatch(name) or name in seen:
            raise EvalError("routing scenario names must be unique semantic kebab-case")
        seen.add(name)
        owner = _text(row.get("owner"), f"{name}.owner")
        if owner not in owners or not (ROOT / owner).is_file():
            raise EvalError(f"{name}: owner is not a current canonical source")
        route = _text(row.get("expected_route"), f"{name}.expected_route")
        if route not in routes:
            raise EvalError(f"{name}: expected route is not current")
        if row.get("split") not in SPLITS:
            raise EvalError(f"{name}: invalid split")
        result.append({**row, "platforms": list(platforms)})
    covered = {row["expected_route"] for row in result}
    missing = routes - covered
    if missing:
        raise EvalError(f"routing scenarios do not cover changed/reasserted routes: {sorted(missing)}")
    return result


def validate_pair_manifest(path: Path = ROUTING_MANIFEST) -> list[dict[str, Any]]:
    """Compatibility alias for callers; scenarios are no longer forced into pairs."""

    return validate_routing_manifest(path)


def selected_cases(selection: str) -> list[dict[str, Any]]:
    if selection not in {*SPLITS, "all"}:
        raise EvalError(f"unknown selection: {selection}")
    validate_semantic_sources(ROOT)
    rows = validate_routing_manifest()
    return [
        {
            "id": row["name"],
            "split": row["split"],
            "platforms": row["platforms"],
            "prompt": row["prompt"],
            "expected": {"route": row["expected_route"]},
            "producers": [{"class": "semantic-owner", "source": row["owner"]}],
        }
        for row in rows
        if selection == "all" or row["split"] == selection
    ]


def validate_case(value: Any, _known_rubrics: set[str] | None = None) -> dict[str, Any]:
    data = load_json(value) if isinstance(value, Path) else value
    required = {"id", "split", "platforms", "prompt", "expected", "producers"}
    if not isinstance(data, dict) or set(data) != required:
        raise EvalError("semantic case has an invalid shape")
    if data["split"] not in SPLITS or set(data["platforms"]) != PLATFORMS:
        raise EvalError("semantic case split or platforms are invalid")
    return data


def validate_rubrics() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "evals/teamwork/rubrics").glob("*.json")):
        value = load_json(path)
        if isinstance(value, dict):
            result[path.stem] = value
    return result


def validate_bound_producer_sources(
    case: dict[str, Any], _path: Path, source_overrides: dict[str, str] | None = None,
) -> None:
    for producer in case.get("producers", []):
        source = producer.get("source")
        if not isinstance(source, str) or not (ROOT / source).is_file():
            raise EvalError("semantic case producer is not a current source")
        if source_overrides is not None and source in source_overrides and not source_overrides[source].strip():
            raise EvalError("semantic owner source is empty")
