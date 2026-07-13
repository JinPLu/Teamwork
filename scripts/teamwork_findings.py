#!/usr/bin/env python3
"""Validate deterministic Teamwork review Finding-state JSON documents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


FINDING_TYPES = ("BLOCKER", "FOLLOW-UP", "SUGGESTION", "SCOPE_DELTA")
FINDING_STATUSES = ("OPEN", "RESOLVED", "WAIVED")
REVIEW_KINDS = ("full", "delta")
DELTA_PROVENANCE = ("prior", "fix_regression", "new_direct_evidence")
VERDICTS = ("ACCEPT", "REVISE", "BLOCKED")


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_findings(document: Any) -> list[str]:
    """Return deterministic validation errors for a review findings document."""

    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document must be an object"]

    review = document.get("review")
    if not isinstance(review, dict):
        errors.append("review must be an object")
        review = {}
    for field in ("id", "contract_id"):
        if not _non_empty_string(review.get(field)):
            errors.append(f"review.{field} must be a non-empty string")
    if not _positive_integer(review.get("contract_version")):
        errors.append("review.contract_version must be a positive integer")
    kind = review.get("kind")
    if kind not in REVIEW_KINDS:
        errors.append("review.kind must be one of: full, delta")
    if kind == "delta":
        if review.get("recheck_number") != 1:
            errors.append("a corrective delta review must have recheck_number 1")
        reviewer_id = review.get("reviewer_id")
        if not _non_empty_string(reviewer_id):
            errors.append("review.reviewer_id must be a non-empty string for a delta review")
        base_reviewer_id = review.get("base_reviewer_id")
        if not _non_empty_string(base_reviewer_id):
            errors.append("review.base_reviewer_id must be a non-empty string for a delta review")
        elif _non_empty_string(reviewer_id) and reviewer_id != base_reviewer_id:
            errors.append("a corrective delta review must use the same reviewer as its base review")
        if not _non_empty_string(review.get("base_review_id")):
            errors.append("review.base_review_id must be a non-empty string for a delta review")
        if review.get("base_review_kind") != "full":
            errors.append("a corrective delta review must be based on a full review, not another delta review")
        base_version = review.get("base_contract_version")
        if not _positive_integer(base_version):
            errors.append("review.base_contract_version must be a positive integer for a delta review")
        elif _positive_integer(review.get("contract_version")) and base_version != review["contract_version"]:
            errors.append("a corrective delta review must keep the same contract version")
        base_finding_ids = review.get("base_finding_ids")
        if not isinstance(base_finding_ids, list) or not all(
            _non_empty_string(finding_id) for finding_id in base_finding_ids
        ):
            errors.append("review.base_finding_ids must be a list of non-empty strings for a delta review")
            base_finding_ids = []
        elif len(base_finding_ids) != len(set(base_finding_ids)):
            errors.append("review.base_finding_ids must be unique")
        declared_fix_ids = review.get("declared_fix_ids")
        if not isinstance(declared_fix_ids, list) or not all(
            _non_empty_string(fix_id) for fix_id in declared_fix_ids
        ):
            errors.append("review.declared_fix_ids must be a list of non-empty strings for a delta review")
            declared_fix_ids = []
        elif len(declared_fix_ids) != len(set(declared_fix_ids)):
            errors.append("review.declared_fix_ids must be unique")
    else:
        base_finding_ids = []
        declared_fix_ids = []

    findings = document.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []
    ids: set[str] = set()
    open_blockers = 0
    for index, finding in enumerate(findings):
        label = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{label} must be an object")
            continue
        finding_id = finding.get("id")
        if not _non_empty_string(finding_id):
            errors.append(f"{label}.id must be a non-empty string")
        elif finding_id in ids:
            errors.append(f"duplicate finding id: {finding_id}")
        else:
            ids.add(finding_id)
        finding_type = finding.get("type")
        if finding_type not in FINDING_TYPES:
            errors.append(f"{label}.type must be one of: {', '.join(FINDING_TYPES)}")
        status = finding.get("status")
        if status not in FINDING_STATUSES:
            errors.append(f"{label}.status must be one of: {', '.join(FINDING_STATUSES)}")
        if "ac_id" in finding and not _non_empty_string(finding["ac_id"]):
            errors.append(f"{label}.ac_id must be a non-empty string when present")
        if kind == "delta":
            provenance = finding.get("provenance")
            if provenance not in DELTA_PROVENANCE:
                errors.append(
                    f"{label}.provenance must be one of: {', '.join(DELTA_PROVENANCE)}"
                )
            elif provenance == "prior" and finding_id not in base_finding_ids:
                errors.append(f"{label} marked prior must reuse a base finding id")
            elif provenance != "prior" and finding_id in base_finding_ids:
                errors.append(f"{label} with new evidence must use a new finding id")
            elif provenance != "prior":
                related_finding_id = finding.get("related_finding_id")
                if related_finding_id not in base_finding_ids:
                    errors.append(
                        f"{label} with new evidence must explicitly relate to a base finding id"
                    )
                if provenance == "fix_regression" and finding.get(
                    "declared_fix_id"
                ) not in declared_fix_ids:
                    errors.append(
                        f"{label} marked fix_regression must reference review.declared_fix_ids"
                    )
        if finding_type == "BLOCKER" and status == "OPEN":
            open_blockers += 1

    verdict = document.get("verdict")
    if verdict not in VERDICTS:
        errors.append("verdict must be one of: ACCEPT, REVISE, BLOCKED")
    elif open_blockers and verdict == "ACCEPT":
        errors.append("verdict must not be ACCEPT while an open BLOCKER exists")
    elif not open_blockers and verdict != "ACCEPT":
        errors.append("verdict must be ACCEPT when no open BLOCKER exists")
    return errors


def findings_summary(document: dict[str, Any]) -> dict[str, Any]:
    findings = document["findings"]
    return {
        "findings": len(findings),
        "ok": True,
        "open_blockers": sum(
            finding["type"] == "BLOCKER" and finding["status"] == "OPEN" for finding in findings
        ),
        "review_id": document["review"]["id"],
        "verdict": document["verdict"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate a review findings JSON file")
    validate.add_argument("path", type=Path)
    validate.add_argument("--summary", action="store_true", help="emit a compact success summary")
    args = parser.parse_args(argv)

    try:
        document = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"errors": [str(exc)], "ok": False}, sort_keys=True), file=sys.stderr)
        return 2
    errors = validate_findings(document)
    if errors:
        print(json.dumps({"errors": errors, "ok": False}, sort_keys=True), file=sys.stderr)
        return 1
    output: dict[str, Any] = findings_summary(document) if args.summary else {"ok": True}
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
