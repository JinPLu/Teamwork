#!/usr/bin/env python3
"""Focused tests for deterministic review Finding-state validation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from teamwork_findings import validate_findings  # noqa: E402


def valid_findings() -> dict[str, object]:
    return {
        "review": {
            "id": "REV-42",
            "contract_id": "TASK-42",
            "contract_version": 1,
            "kind": "delta",
            "recheck_number": 1,
            "reviewer_id": "reviewer-1",
            "base_reviewer_id": "reviewer-1",
            "base_review_id": "REV-41",
            "base_review_kind": "full",
            "base_contract_version": 1,
            "base_finding_ids": ["F-1"],
            "declared_fix_ids": ["FIX-1"],
        },
        "findings": [
            {
                "id": "F-1",
                "type": "FOLLOW-UP",
                "status": "RESOLVED",
                "ac_id": "AC-1",
                "provenance": "prior",
            }
        ],
        "verdict": "ACCEPT",
    }


class FindingStateTests(unittest.TestCase):
    def test_valid_delta_review_with_no_open_blocker_accepts(self) -> None:
        self.assertEqual(validate_findings(valid_findings()), [])

    def test_ids_vocabularies_and_delta_provenance_are_enforced(self) -> None:
        document = valid_findings()
        document["review"] = {"id": "REV-42", "contract_id": "TASK-42", "contract_version": 1, "kind": "delta"}
        document["findings"] = [
            {"id": "F-1", "type": "UNKNOWN", "status": "OPEN"},
            {"id": "F-1", "type": "FOLLOW-UP", "status": "UNKNOWN"},
        ]
        errors = validate_findings(document)
        self.assertIn("review.base_review_id must be a non-empty string for a delta review", errors)
        self.assertIn("review.reviewer_id must be a non-empty string for a delta review", errors)
        self.assertIn("review.base_reviewer_id must be a non-empty string for a delta review", errors)
        self.assertIn("a corrective delta review must be based on a full review, not another delta review", errors)
        self.assertIn("review.base_contract_version must be a positive integer for a delta review", errors)
        self.assertIn("findings[0].type must be one of: BLOCKER, FOLLOW-UP, SUGGESTION, SCOPE_DELTA", errors)
        self.assertIn("findings[1].status must be one of: OPEN, RESOLVED, WAIVED", errors)
        self.assertIn("duplicate finding id: F-1", errors)

    def test_verdict_tracks_open_blockers(self) -> None:
        document = valid_findings()
        document["findings"] = [
            {
                "id": "F-1",
                "type": "BLOCKER",
                "status": "OPEN",
                "provenance": "prior",
            }
        ]
        errors = validate_findings(document)
        self.assertIn("verdict must not be ACCEPT while an open BLOCKER exists", errors)

        document["findings"] = []
        document["verdict"] = "REVISE"
        errors = validate_findings(document)
        self.assertIn("verdict must be ACCEPT when no open BLOCKER exists", errors)

    def test_delta_review_rejects_unrelated_new_blocker_and_requires_declared_fix(self) -> None:
        document = valid_findings()
        document["findings"] = [
            {"id": "F-2", "type": "BLOCKER", "status": "OPEN"}
        ]
        document["verdict"] = "REVISE"
        errors = validate_findings(document)
        self.assertTrue(any("provenance" in error for error in errors))

        document["findings"][0]["provenance"] = "fix_regression"
        errors = validate_findings(document)
        self.assertIn(
            "findings[0] with new evidence must explicitly relate to a base finding id",
            errors,
        )
        self.assertIn(
            "findings[0] marked fix_regression must reference review.declared_fix_ids",
            errors,
        )

        document["findings"][0]["related_finding_id"] = "F-1"
        document["findings"][0]["declared_fix_id"] = "FIX-1"
        self.assertEqual(validate_findings(document), [])

    def test_delta_review_requires_same_reviewer_and_disallows_recursive_delta(self) -> None:
        document = valid_findings()
        document["review"]["base_reviewer_id"] = "reviewer-0"
        document["review"]["base_review_kind"] = "delta"
        document["review"]["recheck_number"] = 2
        errors = validate_findings(document)
        self.assertIn(
            "a corrective delta review must use the same reviewer as its base review", errors
        )
        self.assertIn(
            "a corrective delta review must be based on a full review, not another delta review",
            errors,
        )
        self.assertIn("a corrective delta review must have recheck_number 1", errors)

    def test_fix_regression_must_reference_a_declared_fix(self) -> None:
        document = valid_findings()
        document["findings"] = [
            {
                "id": "F-2",
                "type": "BLOCKER",
                "status": "OPEN",
                "provenance": "fix_regression",
                "related_finding_id": "F-1",
                "declared_fix_id": "FIX-NOT-DECLARED",
            }
        ]
        document["verdict"] = "REVISE"
        self.assertIn(
            "findings[0] marked fix_regression must reference review.declared_fix_ids",
            validate_findings(document),
        )

    def test_new_direct_evidence_must_still_be_related_to_the_base_finding(self) -> None:
        document = valid_findings()
        document["findings"] = [
            {
                "id": "F-2",
                "type": "BLOCKER",
                "status": "OPEN",
                "provenance": "new_direct_evidence",
            }
        ]
        document["verdict"] = "REVISE"
        errors = validate_findings(document)
        self.assertIn(
            "findings[0] with new evidence must explicitly relate to a base finding id",
            errors,
        )

    def test_cli_emits_compact_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "findings.json"
            path.write_text(json.dumps(valid_findings()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "teamwork_findings.py"), "validate", str(path), "--summary"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {"findings": 1, "ok": True, "open_blockers": 0, "review_id": "REV-42", "verdict": "ACCEPT"},
        )


if __name__ == "__main__":
    unittest.main()
