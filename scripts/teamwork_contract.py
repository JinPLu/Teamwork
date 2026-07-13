#!/usr/bin/env python3
"""Validate a compact, deterministic Teamwork Task Contract JSON document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _criterion_ids(document: dict[str, Any]) -> set[str]:
    criteria = document.get("acceptance_criteria")
    if not isinstance(criteria, list):
        return set()
    return {
        criterion["id"]
        for criterion in criteria
        if isinstance(criterion, dict) and _non_empty_string(criterion.get("id"))
    }


def _criteria_by_id(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    criteria = document.get("acceptance_criteria")
    if not isinstance(criteria, list):
        return {}
    return {
        criterion["id"]: criterion
        for criterion in criteria
        if isinstance(criterion, dict) and _non_empty_string(criterion.get("id"))
    }


def validate_contract_transition(document: Any, prior_contract: Any) -> list[str]:
    """Validate a one-step Contract transition against its prior Contract."""

    errors: list[str] = []
    if not isinstance(document, dict) or not isinstance(prior_contract, dict):
        return ["current and prior contracts must be objects"]

    task = document.get("task")
    prior_task = prior_contract.get("task")
    if not isinstance(task, dict) or not isinstance(prior_task, dict):
        return ["current and prior contracts must contain task objects"]
    if task.get("id") != prior_task.get("id"):
        errors.append("transition task.id must equal prior task.id")
    if (
        _positive_integer(task.get("version"))
        and _positive_integer(prior_task.get("version"))
        and task["version"] != prior_task["version"] + 1
    ):
        errors.append("transition task.version must advance exactly one from prior task.version")

    current_ids = _criterion_ids(document)
    prior_ids = _criterion_ids(prior_contract)
    shared_ids = current_ids & prior_ids
    if prior_ids and not shared_ids:
        errors.append("transition must retain at least one prior acceptance criterion id")

    current_criteria = _criteria_by_id(document)
    prior_criteria = _criteria_by_id(prior_contract)
    changed_ids = (current_ids ^ prior_ids) | {
        criterion_id
        for criterion_id in shared_ids
        if current_criteria[criterion_id] != prior_criteria[criterion_id]
    }
    delta = document.get("scope_delta")
    declared_changes = set(delta.get("changes", [])) if isinstance(delta, dict) else set()
    for criterion_id in sorted(changed_ids - declared_changes):
        errors.append(
            f"transition acceptance criterion change must be explicitly listed in scope_delta.changes: {criterion_id}"
        )
    return errors


def validate_contract(document: Any, prior_contract: Any | None = None) -> list[str]:
    """Return deterministic validation errors for a Task Contract document."""

    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document must be an object"]

    task = document.get("task")
    if not isinstance(task, dict):
        errors.append("task must be an object")
        task = {}
    if not _non_empty_string(task.get("id")):
        errors.append("task.id must be a non-empty string")
    if not _positive_integer(task.get("version")):
        errors.append("task.version must be a positive integer")

    for field in ("goal", "decision", "authority", "stop"):
        if not _non_empty_string(document.get(field)):
            errors.append(f"{field} must be a non-empty string")

    scope = document.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
        scope = {}
    for field in ("in", "out", "protected"):
        values = scope.get(field)
        if not isinstance(values, list) or not all(_non_empty_string(value) for value in values):
            errors.append(f"scope.{field} must be a list of non-empty strings")
        elif field == "in" and not values:
            errors.append("scope.in must be non-empty")

    for field in ("invariants", "open_blockers", "replan_triggers"):
        values = document.get(field)
        if not isinstance(values, list) or not all(_non_empty_string(value) for value in values):
            errors.append(f"{field} must be a list of non-empty strings")

    version = task.get("version")
    delta = document.get("scope_delta")
    if version == 1:
        if delta is not None:
            errors.append("scope_delta must be absent for initial task.version 1")
    elif _positive_integer(version):
        if not isinstance(delta, dict):
            errors.append("scope_delta must be an object when task.version is greater than 1")
            delta = {}
        from_version = delta.get("from_version")
        to_version = delta.get("to_version")
        if not _positive_integer(from_version):
            errors.append("scope_delta.from_version must be a positive integer")
        if not _positive_integer(to_version):
            errors.append("scope_delta.to_version must be a positive integer")
        if _positive_integer(to_version) and to_version != version:
            errors.append("scope_delta.to_version must equal task.version")
        if _positive_integer(from_version) and _positive_integer(to_version) and to_version != from_version + 1:
            errors.append("scope_delta must advance exactly one version")
        changes = delta.get("changes")
        if not isinstance(changes, list) or not all(_non_empty_string(change) for change in changes):
            errors.append("scope_delta.changes must be a list of non-empty strings")
        elif not changes:
            errors.append("scope_delta.changes must be non-empty for a version advance")
        for field in ("reason", "acceptance_impact", "next_action"):
            if not _non_empty_string(delta.get(field)):
                errors.append(f"scope_delta.{field} must be a non-empty string")

    criteria = document.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append("acceptance_criteria must be a non-empty list")
        return errors

    ids: set[str] = set()
    for index, criterion in enumerate(criteria):
        label = f"acceptance_criteria[{index}]"
        if not isinstance(criterion, dict):
            errors.append(f"{label} must be an object")
            continue
        criterion_id = criterion.get("id")
        if not _non_empty_string(criterion_id):
            errors.append(f"{label}.id must be a non-empty string")
        elif criterion_id in ids:
            errors.append(f"duplicate acceptance criterion id: {criterion_id}")
        else:
            ids.add(criterion_id)
        for field in ("change", "evidence", "verification"):
            if not _non_empty_string(criterion.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")
    if _positive_integer(version) and version > 1 and prior_contract is None:
        errors.append("prior contract must be provided when task.version is greater than 1")
    if prior_contract is not None:
        errors.extend(validate_contract_transition(document, prior_contract))
    return errors


def contract_summary(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "acceptance_criteria": len(document["acceptance_criteria"]),
        "ok": True,
        "task_id": document["task"]["id"],
        "version": document["task"]["version"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate a Task Contract JSON file")
    validate.add_argument("path", type=Path)
    validate.add_argument("--prior", type=Path, help="validate this Contract as a transition from a prior Contract")
    validate.add_argument("--summary", action="store_true", help="emit a compact success summary")
    args = parser.parse_args(argv)

    try:
        document = json.loads(args.path.read_text(encoding="utf-8"))
        prior_contract = json.loads(args.prior.read_text(encoding="utf-8")) if args.prior else None
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"errors": [str(exc)], "ok": False}, sort_keys=True), file=sys.stderr)
        return 2
    errors = validate_contract(document, prior_contract)
    if errors:
        print(json.dumps({"errors": errors, "ok": False}, sort_keys=True), file=sys.stderr)
        return 1
    output: dict[str, Any] = contract_summary(document) if args.summary else {"ok": True}
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
