"""Validate semantic positive/negative routing pairs and small eval ledgers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from teamwork_tooling.topology import agent_template_paths, public_skill_paths

from .contracts import (
    EvalError,
    ID_RE,
    OPTIMIZER_DECISIONS,
    OPTIMIZER_GATE_DECISIONS,
    OPTIMIZER_KINDS,
    PAIR_MANIFEST,
    PLATFORMS,
    ROOT,
    SPLITS,
)
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


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{label} must be a non-empty string")
    return value


def _owner_paths() -> set[str]:
    return {
        "scripts/install/policy.sh",
        *public_skill_paths(ROOT).values(),
        *(path for mapping in agent_template_paths(ROOT).values() for path in mapping.values()),
    }


def _validate_arm(value: Any, pair_id: str, polarity: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"prompt", "expected_route"}:
        raise EvalError(f"routing pair {pair_id} {polarity} arm must contain prompt and expected_route")
    return {
        "prompt": _nonempty_string(value.get("prompt"), f"routing pair {pair_id} {polarity}.prompt"),
        "expected_route": _nonempty_string(
            value.get("expected_route"), f"routing pair {pair_id} {polarity}.expected_route"
        ),
    }


def validate_pair_manifest(path: Path = PAIR_MANIFEST) -> list[dict[str, Any]]:
    value = load_json(path)
    if not isinstance(value, dict) or set(value) != {"schema_version", "platforms", "pairs"}:
        raise EvalError(f"{display_path(path)}: manifest must contain schema_version, platforms, and pairs")
    if value.get("schema_version") != 1:
        raise EvalError(f"{display_path(path)}: schema_version must be 1")
    platforms = value.get("platforms")
    if not isinstance(platforms, list) or set(platforms) != PLATFORMS or len(platforms) != len(set(platforms)):
        raise EvalError(f"{display_path(path)}: platforms must match the supported host set")
    rows = value.get("pairs")
    if not isinstance(rows, list) or not rows:
        raise EvalError(f"{display_path(path)}: pairs must be a non-empty list")
    owners = _owner_paths()
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "split", "owner", "positive", "negative"}:
            raise EvalError(f"{display_path(path)}: each pair has an invalid shape")
        pair_id = _nonempty_string(row.get("id"), "routing pair id")
        if not ID_RE.fullmatch(pair_id) or pair_id in seen:
            raise EvalError(f"{display_path(path)}: pair ids must be unique kebab-case strings")
        seen.add(pair_id)
        split = row.get("split")
        if split not in SPLITS:
            raise EvalError(f"routing pair {pair_id}: invalid split")
        owner = _nonempty_string(row.get("owner"), f"routing pair {pair_id}.owner")
        if owner not in owners or not (ROOT / owner).is_file():
            raise EvalError(f"routing pair {pair_id}: owner is not an active topology source: {owner}")
        positive = _validate_arm(row.get("positive"), pair_id, "positive")
        negative = _validate_arm(row.get("negative"), pair_id, "negative")
        if positive["expected_route"] == negative["expected_route"]:
            raise EvalError(f"routing pair {pair_id}: positive and negative routes must differ")
        result.append({
            "id": pair_id,
            "split": split,
            "owner": owner,
            "platforms": list(platforms),
            "positive": positive,
            "negative": negative,
        })
    _validate_coverage(result)
    return result


def _validate_coverage(pairs: list[dict[str, Any]]) -> None:
    expected_skills = set(public_skill_paths(ROOT))
    positive_routes = {row["positive"]["expected_route"] for row in pairs}
    missing = expected_skills - positive_routes
    if missing:
        raise EvalError(f"routing pairs lack positive coverage for public skills: {sorted(missing)}")
    if not {row["split"] for row in pairs} == SPLITS:
        raise EvalError("routing pairs must cover dev and release splits")


def _flatten_pair(row: dict[str, Any], polarity: str) -> dict[str, Any]:
    arm = row[polarity]
    return {
        "id": f"{row['id']}-{polarity}",
        "pair_id": row["id"],
        "polarity": polarity,
        "split": row["split"],
        "platforms": list(row["platforms"]),
        "prompt": arm["prompt"],
        "expected": {"route": arm["expected_route"]},
        "producers": [{"class": "semantic-owner", "source": row["owner"]}],
    }


def selected_cases(selection: str) -> list[dict[str, Any]]:
    if selection not in {*SPLITS, "all"}:
        raise EvalError(f"unknown selection: {selection}")
    validate_semantic_sources(ROOT)
    pairs = validate_pair_manifest()
    cases = [
        _flatten_pair(row, polarity)
        for row in pairs
        if selection == "all" or row["split"] == selection
        for polarity in ("positive", "negative")
    ]
    if not cases:
        raise EvalError(f"selection {selection!r} has no cases")
    return cases


def validate_case(value: Any, _known_rubrics: set[str] | None = None) -> dict[str, Any]:
    """Validate one flattened semantic case; retained for small external harnesses."""

    data = load_json(value) if isinstance(value, Path) else value
    required = {"id", "pair_id", "polarity", "split", "platforms", "prompt", "expected", "producers"}
    if not isinstance(data, dict) or set(data) != required:
        raise EvalError("semantic case has an invalid shape")
    if data["polarity"] not in {"positive", "negative"} or data["split"] not in SPLITS:
        raise EvalError("semantic case polarity or split is invalid")
    if set(data["platforms"]) != PLATFORMS:
        raise EvalError("semantic case platforms are incomplete")
    if not isinstance(data["expected"], dict) or set(data["expected"]) != {"route"}:
        raise EvalError("semantic case expected value must contain one route")
    return data


def validate_rubrics() -> dict[str, dict[str, Any]]:
    """Load rubrics as telemetry; routing correctness is defined by semantic pairs."""

    result: dict[str, dict[str, Any]] = {}
    rubric_dir = ROOT / "evals/teamwork/rubrics"
    for path in sorted(rubric_dir.glob("*.json")):
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
            raise EvalError("semantic case producer is not an active source")
        if source_overrides is not None and source in source_overrides and not source_overrides[source].strip():
            raise EvalError("semantic owner source is empty")


def _required_fields(entry: dict[str, Any], path: Path, index: int, schema: set[str]) -> None:
    missing = schema - set(entry)
    if missing:
        raise EvalError(f"{display_path(path)}:{index}: missing ledger fields: {sorted(missing)}")


def validate_ledger_lines(path: Path, name: str, schema: set[str]) -> int:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        raise EvalError(f"cannot read ledger {display_path(path)}: {exc}") from exc
    if not lines:
        raise EvalError(f"{display_path(path)}: ledger must not be empty")
    entries: list[dict[str, Any]] = []
    for index, line in enumerate(lines, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{display_path(path)}:{index}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise EvalError(f"{display_path(path)}:{index}: ledger entry must be an object")
        entries.append(value)
        _required_fields(value, path, index, schema)
        if name == "optimizer-candidates.jsonl":
            if value.get("kind") not in OPTIMIZER_KINDS:
                raise EvalError(f"{display_path(path)}:{index}: invalid optimizer kind")
            if value.get("gate_decision") not in OPTIMIZER_GATE_DECISIONS:
                raise EvalError(f"{display_path(path)}:{index}: invalid gate_decision")
            if value.get("decision") not in OPTIMIZER_DECISIONS:
                raise EvalError(f"{display_path(path)}:{index}: invalid decision")
    return len(entries)
