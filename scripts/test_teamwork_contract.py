#!/usr/bin/env python3
"""Focused tests for the deterministic Task Contract validator."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from teamwork_contract import validate_contract  # noqa: E402


def valid_contract() -> dict[str, object]:
    return {
        "task": {"id": "TASK-42", "version": 1},
        "goal": "Make review convergence deterministic.",
        "decision": "Use one full review and one same-thread delta recheck.",
        "scope": {
            "in": ["Task Contract and Finding validators."],
            "out": ["Live model evaluation."],
            "protected": ["Authorization boundaries."],
        },
        "invariants": ["No open BLOCKER means ACCEPT."],
        "authority": "Local in-scope edits and focused tests.",
        "open_blockers": [],
        "replan_triggers": ["An accepted Scope Delta."],
        "stop": "Focused tests and package validation pass.",
        "acceptance_criteria": [
            {
                "id": "AC-1",
                "change": "Add the validator.",
                "evidence": "Focused unit test output.",
                "verification": "python3 scripts/test_teamwork_contract.py",
            }
        ],
    }


def valid_transition() -> dict[str, object]:
    contract = valid_contract()
    contract["task"] = {"id": "TASK-42", "version": 2}
    contract["scope_delta"] = {
        "from_version": 1,
        "to_version": 2,
        "changes": ["AC-2"],
        "reason": "A new acceptance criterion is needed.",
        "acceptance_impact": "Adds AC-2.",
        "next_action": "Verify AC-2 with focused tests.",
    }
    contract["acceptance_criteria"].append(
        {
            "id": "AC-2",
            "change": "Validate transitions against the prior Contract.",
            "evidence": "Focused transition test output.",
            "verification": "python3 scripts/test_teamwork_contract.py",
        }
    )
    return contract


class TaskContractTests(unittest.TestCase):
    def test_valid_contract_has_no_errors(self) -> None:
        self.assertEqual(validate_contract(valid_contract()), [])

    def test_required_identity_version_and_ac_mapping_are_enforced(self) -> None:
        contract = valid_contract()
        del contract["task"]
        contract["acceptance_criteria"] = [
            {"id": "AC-1", "change": "x", "evidence": "y", "verification": "z"},
            {"id": "AC-1", "change": "x", "evidence": "y", "verification": "z"},
        ]
        errors = validate_contract(contract)
        self.assertTrue(any("task" in error for error in errors))
        self.assertTrue(any("duplicate acceptance criterion id: AC-1" == error for error in errors))

    def test_scope_delta_must_advance_exactly_one_version_and_match_task(self) -> None:
        contract = valid_contract()
        contract["task"] = {"id": "TASK-42", "version": 3}
        contract["scope_delta"] = {
            "from_version": 1,
            "to_version": 3,
            "changes": [],
            "reason": "The accepted scope changed.",
            "acceptance_impact": "AC-1 changed.",
            "next_action": "Replan AC-1.",
        }
        errors = validate_contract(contract)
        self.assertIn("scope_delta must advance exactly one version", errors)
        self.assertIn("scope_delta.changes must be non-empty for a version advance", errors)

    def test_initial_contract_must_not_claim_a_scope_delta(self) -> None:
        contract = valid_contract()
        contract["scope_delta"] = {
            "from_version": 0,
            "to_version": 1,
            "changes": ["Initial scope."],
        }
        self.assertIn(
            "scope_delta must be absent for initial task.version 1",
            validate_contract(contract),
        )

    def test_transition_rejects_changed_task_id_and_replaced_ac_ids(self) -> None:
        prior = valid_contract()
        current = valid_transition()
        current["task"] = {"id": "TASK-99", "version": 3}
        current["acceptance_criteria"] = [
            {
                "id": "AC-9",
                "change": "Replace all original criteria.",
                "evidence": "None.",
                "verification": "None.",
            }
        ]
        errors = validate_contract(current, prior)
        self.assertIn("transition task.id must equal prior task.id", errors)
        self.assertIn(
            "transition task.version must advance exactly one from prior task.version",
            errors,
        )
        self.assertIn("transition must retain at least one prior acceptance criterion id", errors)
        self.assertIn(
            "transition acceptance criterion change must be explicitly listed in scope_delta.changes: AC-1",
            errors,
        )
        self.assertIn(
            "transition acceptance criterion change must be explicitly listed in scope_delta.changes: AC-9",
            errors,
        )

    def test_transition_accepts_explicit_delta_for_changed_ac(self) -> None:
        self.assertEqual(validate_contract(valid_transition(), valid_contract()), [])

    def test_later_contract_requires_prior_contract(self) -> None:
        self.assertIn(
            "prior contract must be provided when task.version is greater than 1",
            validate_contract(valid_transition()),
        )

    def test_cli_emits_compact_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "current.json"
            prior = Path(temporary) / "prior.json"
            path.write_text(json.dumps(valid_transition()), encoding="utf-8")
            prior.write_text(json.dumps(valid_contract()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "teamwork_contract.py"),
                    "validate",
                    str(path),
                    "--prior",
                    str(prior),
                    "--summary",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {"acceptance_criteria": 2, "ok": True, "task_id": "TASK-42", "version": 2},
        )


if __name__ == "__main__":
    unittest.main()
