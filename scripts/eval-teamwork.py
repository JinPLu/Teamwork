#!/usr/bin/env python3
"""Validate Teamwork eval fixtures without network or model dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "evals" / "teamwork"
CASE_DIR = EVAL_ROOT / "cases"
RUBRIC_DIR = EVAL_ROOT / "rubrics"
LEDGER_DIR = EVAL_ROOT / "ledgers"

REQUIRED_CASE_FIELDS = {
    "id",
    "split",
    "source",
    "target",
    "platforms",
    "prompt",
    "expected",
    "must",
    "must_not",
    "evidence",
}
SPLITS = {"dev", "release"}
SOURCES = {"synthetic", "trajectory", "bug", "review", "release"}
PLATFORMS = {"codex", "cursor", "claude"}
TARGET_PREFIXES = ("skills/", "evals/teamwork/", "scripts/eval-teamwork.py")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEDGER_SCHEMAS = {
    "accepted.jsonl": {
        "date",
        "change_id",
        "surface",
        "decision",
        "reason",
        "cases",
        "validation",
        "reviewer",
    },
    "rejected.jsonl": {
        "date",
        "proposal",
        "surface",
        "reason",
        "risk",
        "replacement",
    },
    "harness-candidates.jsonl": {
        "date",
        "candidate_id",
        "owned_files",
        "hypothesis",
        "baseline",
        "candidate_result",
        "decision",
        "rollback",
    },
}


class EvalError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise EvalError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def require_string(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{path.relative_to(ROOT)}: {field} must be a non-empty string")
    return value


def require_string_list(value: Any, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise EvalError(f"{path.relative_to(ROOT)}: {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise EvalError(f"{path.relative_to(ROOT)}: {field} must contain non-empty strings")
    return value


def validate_target(target: str, path: Path) -> None:
    if target.startswith("/") or ".." in Path(target).parts:
        raise EvalError(f"{path.relative_to(ROOT)}: target must be package-relative: {target}")
    if not target.startswith(TARGET_PREFIXES):
        raise EvalError(f"{path.relative_to(ROOT)}: target is not an allowed package surface: {target}")
    target_path = (ROOT / target).resolve()
    try:
        target_path.relative_to(ROOT)
    except ValueError as exc:
        raise EvalError(f"{path.relative_to(ROOT)}: target points outside repo: {target}") from exc
    if not target_path.is_file():
        raise EvalError(f"{path.relative_to(ROOT)}: target does not exist: {target}")


def validate_case(path: Path, known_rubrics: set[str]) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise EvalError(f"{path.relative_to(ROOT)}: case must be a JSON object")
    missing = sorted(REQUIRED_CASE_FIELDS - set(data))
    if missing:
        raise EvalError(f"{path.relative_to(ROOT)}: missing required fields: {', '.join(missing)}")

    case_id = require_string(data["id"], "id", path)
    if not ID_RE.match(case_id):
        raise EvalError(f"{path.relative_to(ROOT)}: id must be kebab-case")

    split = require_string(data["split"], "split", path)
    if split not in SPLITS:
        raise EvalError(f"{path.relative_to(ROOT)}: split must be one of {sorted(SPLITS)}")

    source = require_string(data["source"], "source", path)
    if source not in SOURCES:
        raise EvalError(f"{path.relative_to(ROOT)}: source must be one of {sorted(SOURCES)}")

    target = require_string(data["target"], "target", path)
    validate_target(target, path)

    platforms = require_string_list(data["platforms"], "platforms", path)
    unknown_platforms = sorted(set(platforms) - PLATFORMS)
    if unknown_platforms:
        raise EvalError(f"{path.relative_to(ROOT)}: unknown platforms: {', '.join(unknown_platforms)}")

    require_string(data["prompt"], "prompt", path)
    if not isinstance(data["expected"], dict) or not data["expected"]:
        raise EvalError(f"{path.relative_to(ROOT)}: expected must be a non-empty object")
    require_string_list(data["must"], "must", path)
    require_string_list(data["must_not"], "must_not", path)
    evidence = data["evidence"]
    if not (
        isinstance(evidence, str)
        and evidence.strip()
        or isinstance(evidence, list)
        and evidence
        and all(isinstance(item, str) and item.strip() for item in evidence)
    ):
        raise EvalError(f"{path.relative_to(ROOT)}: evidence must be a non-empty string or string list")

    rubric = data.get("rubric")
    if rubric is not None:
        rubric_id = require_string(rubric, "rubric", path)
        if rubric_id not in known_rubrics:
            raise EvalError(f"{path.relative_to(ROOT)}: unknown rubric: {rubric_id}")
    return data


def validate_rubrics() -> set[str]:
    if not RUBRIC_DIR.is_dir():
        raise EvalError("evals/teamwork/rubrics/ is missing")
    rubrics: set[str] = set()
    for path in sorted(RUBRIC_DIR.glob("*.json")):
        data = load_json(path)
        if not isinstance(data, dict):
            raise EvalError(f"{path.relative_to(ROOT)}: rubric must be a JSON object")
        rubric_id = require_string(data.get("id"), "id", path)
        if rubric_id in rubrics:
            raise EvalError(f"{path.relative_to(ROOT)}: duplicate rubric id: {rubric_id}")
        has_criteria = isinstance(data.get("criteria"), list) and bool(data["criteria"])
        has_dimensions = isinstance(data.get("dimensions"), list) and bool(data["dimensions"])
        if not has_criteria and not has_dimensions:
            raise EvalError(f"{path.relative_to(ROOT)}: rubric must define non-empty criteria or dimensions")
        if "description" in data:
            require_string(data.get("description"), "description", path)
        rubrics.add(rubric_id)
    if not rubrics:
        raise EvalError("no rubrics found")
    return rubrics


def validate_ledgers() -> int:
    if not LEDGER_DIR.is_dir():
        raise EvalError("evals/teamwork/ledgers/ is missing")
    line_count = 0
    for name, required_fields in sorted(LEDGER_SCHEMAS.items()):
        path = LEDGER_DIR / name
        if not path.is_file():
            raise EvalError(f"missing ledger: {path.relative_to(ROOT)}")
        lines = path.read_text().splitlines()
        if not lines:
            raise EvalError(f"{path.relative_to(ROOT)}: ledger must not be empty")
        for index, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvalError(f"{path.relative_to(ROOT)}:{index}: invalid JSONL: {exc}") from exc
            if not isinstance(data, dict):
                raise EvalError(f"{path.relative_to(ROOT)}:{index}: ledger entry must be an object")
            require_string(data.get("date"), "date", path)
            missing = sorted(required_fields - set(data))
            if missing:
                raise EvalError(
                    f"{path.relative_to(ROOT)}:{index}: missing ledger fields: {', '.join(missing)}"
                )
            line_count += 1
    return line_count


def selected_cases(selection: str) -> list[dict[str, Any]]:
    if not CASE_DIR.is_dir():
        raise EvalError("evals/teamwork/cases/ is missing")
    known_rubrics = validate_rubrics()
    validate_ledgers()
    cases = [validate_case(path, known_rubrics) for path in sorted(CASE_DIR.glob("*.json"))]
    if not cases:
        raise EvalError("no cases found")
    seen: set[str] = set()
    for case in cases:
        case_id = case["id"]
        if case_id in seen:
            raise EvalError(f"duplicate case id: {case_id}")
        seen.add(case_id)
    if selection == "all":
        selected = cases
        missing_splits = sorted(split for split in SPLITS if not any(case["split"] == split for case in cases))
        if missing_splits:
            raise EvalError(f"empty split(s): {', '.join(missing_splits)}")
    else:
        selected = [case for case in cases if case["split"] == selection]
    if not selected:
        raise EvalError(f"split {selection!r} has no cases")
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Teamwork eval fixtures.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--split", choices=sorted(SPLITS))
    group.add_argument("--all", action="store_true", help="validate all cases")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selection = "all" if args.all else args.split
    try:
        cases = selected_cases(selection)
    except EvalError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    by_split = {split: 0 for split in SPLITS}
    by_platform = {platform: 0 for platform in PLATFORMS}
    for case in cases:
        by_split[case["split"]] += 1
        for platform in case["platforms"]:
            by_platform[platform] += 1
    detail = ", ".join(f"{split}={count}" for split, count in sorted(by_split.items()) if count)
    summary = {
        "status": "pass",
        "selection": selection,
        "cases": len(cases),
        "by_split": {split: count for split, count in sorted(by_split.items()) if count},
        "by_platform": {platform: count for platform, count in sorted(by_platform.items()) if count},
        "case_ids": [case["id"] for case in cases],
    }
    print(json.dumps(summary, sort_keys=True))
    print(f"OK: Teamwork eval {selection} passed ({len(cases)} cases; {detail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
