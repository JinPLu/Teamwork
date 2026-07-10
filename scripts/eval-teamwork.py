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
OUTPUT_DIR = EVAL_ROOT / "outputs"

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
    "optimizer-candidates.jsonl": {
        "date",
        "candidate_id",
        "kind",
        "provider",
        "model",
        "model_config",
        "prompt_or_template",
        "owned_files",
        "denylist",
        "baseline",
        "treatment",
        "gate_decision",
        "rollback",
        "validation",
        "release_audit",
        "reviewer",
        "decision",
    },
}
OPTIMIZER_KINDS = {"skillopt-lite", "harnessopt-lite"}
OPTIMIZER_GATE_DECISIONS = {"accept_new_best", "accept", "reject", "flat", "blocked"}
OPTIMIZER_DECISIONS = {"candidate", "accepted", "rejected", "blocked"}
PLACEHOLDER = "not_applicable"
GLOB_CHARS = set("*?[")
REQUIRED_QUESTION_FIRST_CASES = {
    "complex-autonomy-control": {
        "inspect_and_proceed",
        "no_grill_ceremony",
        "no_question",
    },
    "question-first-explicit-grill": {
        "ask_one_question",
        "recommended_answer",
        "no_plan",
        "no_edit",
        "no_dispatch",
    },
    "question-first-explicit-lightweight-grill": {
        "ask_one_question",
        "recommended_answer",
        "no_plan",
        "no_edit",
        "no_dispatch",
        "lightweight_grill_override",
    },
    "question-first-complex-uncertainty": {"decision_risk_question", "no_plan_before_question"},
    "question-first-lightweight-control": {
        "direct_lightweight",
        "no_grill_ceremony",
        "no_subagent_dispatch",
        "no_durable_plan",
        "no_question",
    },
}
EXPLICIT_GRILL_CASES = {
    "question-first-explicit-grill",
    "question-first-explicit-lightweight-grill",
}
OUTPUT_REQUIRED_FIELDS = {
    "case_id",
    "platform",
    "input",
    "output",
    "expected_behavior",
    "passed",
    "fail_reason",
}


class EvalError(Exception):
    pass


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise EvalError(f"{display_path(path)}: invalid JSON: {exc}") from exc


def require_string(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{display_path(path)}: {field} must be a non-empty string")
    return value


def require_string_list(value: Any, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise EvalError(f"{display_path(path)}: {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise EvalError(f"{display_path(path)}: {field} must contain non-empty strings")
    return value


def is_package_relative(value: str) -> bool:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    try:
        (ROOT / candidate).resolve().relative_to(ROOT)
    except ValueError:
        return False
    return True


def is_glob_like(value: str) -> bool:
    return any(char in value for char in GLOB_CHARS)


def require_evidence_path(value: Any, field: str, path: Path, index: int) -> str:
    item = require_string(value, field, path)
    if item == PLACEHOLDER:
        raise EvalError(f"{display_path(path)}:{index}: {field} must not be {PLACEHOLDER}")
    if not is_package_relative(item):
        raise EvalError(f"{display_path(path)}:{index}: {field} must be package-relative: {item}")
    item_path = ROOT / item
    if not item_path.exists():
        raise EvalError(f"{display_path(path)}:{index}: {field} path does not exist: {item}")
    return item


def validate_owned_files(items: list[str], path: Path, index: int) -> None:
    for item in items:
        if item == PLACEHOLDER:
            raise EvalError(f"{display_path(path)}:{index}: owned_files must not contain {PLACEHOLDER}")
        if not is_package_relative(item):
            raise EvalError(f"{display_path(path)}:{index}: owned_files entry must be package-relative: {item}")
        if is_glob_like(item):
            continue
        if not (ROOT / item).exists():
            raise EvalError(f"{display_path(path)}:{index}: owned_files path does not exist: {item}")


def validate_target(target: str, path: Path) -> None:
    if target.startswith("/") or ".." in Path(target).parts:
        raise EvalError(f"{display_path(path)}: target must be package-relative: {target}")
    if not target.startswith(TARGET_PREFIXES):
        raise EvalError(f"{display_path(path)}: target is not an allowed package surface: {target}")
    target_path = (ROOT / target).resolve()
    try:
        target_path.relative_to(ROOT)
    except ValueError as exc:
        raise EvalError(f"{display_path(path)}: target points outside repo: {target}") from exc
    if not target_path.is_file():
        raise EvalError(f"{display_path(path)}: target does not exist: {target}")


def validate_case(path: Path, known_rubrics: set[str]) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise EvalError(f"{display_path(path)}: case must be a JSON object")
    missing = sorted(REQUIRED_CASE_FIELDS - set(data))
    if missing:
        raise EvalError(f"{display_path(path)}: missing required fields: {', '.join(missing)}")

    case_id = require_string(data["id"], "id", path)
    if not ID_RE.match(case_id):
        raise EvalError(f"{display_path(path)}: id must be kebab-case")

    split = require_string(data["split"], "split", path)
    if split not in SPLITS:
        raise EvalError(f"{display_path(path)}: split must be one of {sorted(SPLITS)}")

    source = require_string(data["source"], "source", path)
    if source not in SOURCES:
        raise EvalError(f"{display_path(path)}: source must be one of {sorted(SOURCES)}")

    target = require_string(data["target"], "target", path)
    validate_target(target, path)

    platforms = require_string_list(data["platforms"], "platforms", path)
    unknown_platforms = sorted(set(platforms) - PLATFORMS)
    if unknown_platforms:
        raise EvalError(f"{display_path(path)}: unknown platforms: {', '.join(unknown_platforms)}")

    require_string(data["prompt"], "prompt", path)
    if not isinstance(data["expected"], dict) or not data["expected"]:
        raise EvalError(f"{display_path(path)}: expected must be a non-empty object")
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
        raise EvalError(f"{display_path(path)}: evidence must be a non-empty string or string list")

    rubric = data.get("rubric")
    if rubric is not None:
        rubric_id = require_string(rubric, "rubric", path)
        if rubric_id not in known_rubrics:
            raise EvalError(f"{display_path(path)}: unknown rubric: {rubric_id}")
    return data


def validate_rubrics() -> set[str]:
    if not RUBRIC_DIR.is_dir():
        raise EvalError("evals/teamwork/rubrics/ is missing")
    rubrics: set[str] = set()
    for path in sorted(RUBRIC_DIR.glob("*.json")):
        data = load_json(path)
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(path)}: rubric must be a JSON object")
        rubric_id = require_string(data.get("id"), "id", path)
        if rubric_id in rubrics:
            raise EvalError(f"{display_path(path)}: duplicate rubric id: {rubric_id}")
        has_criteria = isinstance(data.get("criteria"), list) and bool(data["criteria"])
        has_dimensions = isinstance(data.get("dimensions"), list) and bool(data["dimensions"])
        if not has_criteria and not has_dimensions:
            raise EvalError(f"{display_path(path)}: rubric must define non-empty criteria or dimensions")
        if "description" in data:
            require_string(data.get("description"), "description", path)
        rubrics.add(rubric_id)
    if not rubrics:
        raise EvalError("no rubrics found")
    return rubrics


def validate_optimizer_candidate_entry(data: dict[str, Any], path: Path, index: int) -> None:
    kind = require_string(data.get("kind"), "kind", path)
    if kind not in OPTIMIZER_KINDS:
        raise EvalError(f"{display_path(path)}:{index}: kind must be one of {sorted(OPTIMIZER_KINDS)}")

    gate_decision = require_string(data.get("gate_decision"), "gate_decision", path)
    if gate_decision not in OPTIMIZER_GATE_DECISIONS:
        raise EvalError(
            f"{display_path(path)}:{index}: gate_decision must be one of {sorted(OPTIMIZER_GATE_DECISIONS)}"
        )

    decision = require_string(data.get("decision"), "decision", path)
    if decision not in OPTIMIZER_DECISIONS:
        raise EvalError(f"{display_path(path)}:{index}: decision must be one of {sorted(OPTIMIZER_DECISIONS)}")

    for field in (
        "candidate_id",
        "provider",
        "model",
        "model_config",
        "release_audit",
        "reviewer",
    ):
        item = require_string(data.get(field), field, path)
        if item == PLACEHOLDER:
            raise EvalError(f"{display_path(path)}:{index}: {field} must not be {PLACEHOLDER}")

    for field in ("prompt_or_template", "baseline", "treatment", "rollback"):
        require_evidence_path(data.get(field), field, path, index)

    owned_files = require_string_list(data.get("owned_files"), "owned_files", path)
    validate_owned_files(owned_files, path, index)

    for field in ("denylist", "validation"):
        items = require_string_list(data.get(field), field, path)
        if field == "validation" and all(item == PLACEHOLDER for item in items):
            raise EvalError(f"{display_path(path)}:{index}: validation must include real evidence")


def validate_ledger_lines(path: Path, name: str, required_fields: set[str]) -> int:
    if not path.is_file():
        raise EvalError(f"missing ledger: {display_path(path)}")
    lines = path.read_text().splitlines()
    if not lines:
        raise EvalError(f"{display_path(path)}: ledger must not be empty")
    line_count = 0
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{display_path(path)}:{index}: invalid JSONL: {exc}") from exc
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(path)}:{index}: ledger entry must be an object")
        require_string(data.get("date"), "date", path)
        missing = sorted(required_fields - set(data))
        if missing:
            raise EvalError(f"{display_path(path)}:{index}: missing ledger fields: {', '.join(missing)}")
        if name == "optimizer-candidates.jsonl":
            validate_optimizer_candidate_entry(data, path, index)
        line_count += 1
    return line_count


def validate_ledgers() -> int:
    if not LEDGER_DIR.is_dir():
        raise EvalError("evals/teamwork/ledgers/ is missing")
    line_count = 0
    for name, required_fields in sorted(LEDGER_SCHEMAS.items()):
        path = LEDGER_DIR / name
        if not path.is_file():
            if name == "optimizer-candidates.jsonl":
                continue
            raise EvalError(f"missing ledger: {display_path(path)}")
        line_count += validate_ledger_lines(path, name, required_fields)
    return line_count


def validate_question_first_outputs(case_ids: set[str]) -> int:
    missing_cases = sorted(set(REQUIRED_QUESTION_FIRST_CASES) - case_ids)
    if missing_cases:
        raise EvalError(f"missing question-first case(s): {', '.join(missing_cases)}")

    output_path = OUTPUT_DIR / "question-first" / "dev.jsonl"
    if not output_path.is_file():
        raise EvalError(f"missing question-first output samples: {display_path(output_path)}")

    seen: set[str] = set()
    seen_platforms: dict[str, set[str]] = {case_id: set() for case_id in REQUIRED_QUESTION_FIRST_CASES}
    rows = 0
    for index, line in enumerate(output_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{display_path(output_path)}:{index}: invalid JSONL: {exc}") from exc
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(output_path)}:{index}: output row must be an object")
        missing = sorted(OUTPUT_REQUIRED_FIELDS - set(data))
        if missing:
            raise EvalError(f"{display_path(output_path)}:{index}: missing output fields: {', '.join(missing)}")

        case_id = require_string(data.get("case_id"), "case_id", output_path)
        if case_id not in REQUIRED_QUESTION_FIRST_CASES:
            raise EvalError(f"{display_path(output_path)}:{index}: unexpected question-first case_id: {case_id}")
        if case_id not in case_ids:
            raise EvalError(f"{display_path(output_path)}:{index}: output references missing case: {case_id}")

        platform = require_string(data.get("platform"), "platform", output_path)
        if platform not in PLATFORMS:
            raise EvalError(f"{display_path(output_path)}:{index}: unknown platform: {platform}")
        require_string(data.get("input"), "input", output_path)
        require_string(data.get("output"), "output", output_path)

        expected = set(require_string_list(data.get("expected_behavior"), "expected_behavior", output_path))
        required = REQUIRED_QUESTION_FIRST_CASES[case_id]
        missing_expected = sorted(required - expected)
        if missing_expected:
            raise EvalError(
                f"{display_path(output_path)}:{index}: expected_behavior missing for {case_id}: "
                f"{', '.join(missing_expected)}"
            )

        passed = data.get("passed")
        if not isinstance(passed, bool):
            raise EvalError(f"{display_path(output_path)}:{index}: passed must be boolean")
        fail_reason = data.get("fail_reason")
        if not isinstance(fail_reason, str):
            raise EvalError(f"{display_path(output_path)}:{index}: fail_reason must be a string")
        if passed and fail_reason:
            raise EvalError(f"{display_path(output_path)}:{index}: passing row must have empty fail_reason")
        if not passed:
            raise EvalError(f"{display_path(output_path)}:{index}: question-first sample failed: {fail_reason}")

        output = data["output"].lower()
        if case_id in EXPLICIT_GRILL_CASES:
            if output.count("question:") != 1 or data["output"].count("?") != 1:
                raise EvalError(f"{display_path(output_path)}:{index}: explicit grill output must ask exactly one question")
            if "facts checked:" not in output or "recommended:" not in output:
                raise EvalError(
                    f"{display_path(output_path)}:{index}: explicit grill output must cite facts and recommend"
                )
            forbidden = (
                "steps:",
                "implementation",
                "edit",
                "dispatch",
                "goal proposal",
                "plan:",
                "planning",
                "subagent",
                "worker",
                "durable plan",
            )
            if any(item in output for item in forbidden):
                raise EvalError(f"{display_path(output_path)}:{index}: explicit grill output contains forbidden enactment")
        if case_id == "question-first-complex-uncertainty":
            if "question:" not in output:
                raise EvalError(f"{display_path(output_path)}:{index}: complex uncertainty output must ask a question")
            if "steps:" in output or "implementation" in output:
                raise EvalError(f"{display_path(output_path)}:{index}: complex uncertainty output planned before asking")
        if case_id == "question-first-lightweight-control":
            ceremony_forbidden = (
                "shared understanding packet",
                "grill",
                "question-first",
            )
            orchestration_forbidden = (
                "question:",
                "dispatch",
                "subagent",
                "worker",
                "durable plan",
                "plan:",
                "planning",
            )
            if "?" in data["output"] or any(item in output for item in ceremony_forbidden):
                raise EvalError(f"{display_path(output_path)}:{index}: lightweight output must not use grill ceremony")
            if any(item in output for item in orchestration_forbidden):
                raise EvalError(f"{display_path(output_path)}:{index}: lightweight output must not plan or dispatch")
            direct_markers = ("directly", "make the one-line", "fix the typo")
            if not any(item in output for item in direct_markers):
                raise EvalError(f"{display_path(output_path)}:{index}: lightweight output must indicate direct action")
        if case_id == "complex-autonomy-control":
            forbidden = (
                "question:",
                "shared understanding packet",
                "grill",
                "question-first",
                "which do you prefer",
                "would you like",
            )
            if "?" in data["output"] or any(item in output for item in forbidden):
                raise EvalError(
                    f"{display_path(output_path)}:{index}: autonomy control must not ask or add grill ceremony"
                )
            proceed_markers = ("inspect", "proceed", "design", "implement")
            if not any(item in output for item in proceed_markers):
                raise EvalError(
                    f"{display_path(output_path)}:{index}: autonomy control must indicate inspection and action"
                )

        seen.add(case_id)
        seen_platforms[case_id].add(platform)
        rows += 1

    missing_outputs = sorted(set(REQUIRED_QUESTION_FIRST_CASES) - seen)
    if missing_outputs:
        raise EvalError(f"missing question-first output row(s): {', '.join(missing_outputs)}")
    for case_id, platforms in sorted(seen_platforms.items()):
        missing_platforms = sorted(PLATFORMS - platforms)
        if missing_platforms:
            raise EvalError(
                f"missing question-first output platform(s) for {case_id}: {', '.join(missing_platforms)}"
            )
    return rows


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
    output_rows = validate_question_first_outputs(seen)
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
    group.add_argument("--optimizer-ledger", type=Path, metavar="PATH", help="validate one optimizer candidate ledger")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.optimizer_ledger:
        path = args.optimizer_ledger.resolve()
        try:
            count = validate_ledger_lines(path, "optimizer-candidates.jsonl", LEDGER_SCHEMAS["optimizer-candidates.jsonl"])
        except EvalError as exc:
            print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"status": "pass", "selection": "optimizer-ledger", "rows": count}, sort_keys=True))
        print(f"OK: optimizer ledger passed ({count} rows)")
        return 0

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
