#!/usr/bin/env python3
"""Compatibility checks for the modular deterministic eval implementation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval-teamwork.py"
sys.path.insert(0, str(SCRIPT.parent))

from teamwork_tooling.evaluation.cases import selected_cases, validate_ledger_lines
from teamwork_tooling.evaluation.contracts import EvalError


class EvalTeamworkCompatibilityTests(unittest.TestCase):
    def run_eval(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )

    def test_help_output_preserves_public_semantics_across_python_versions(self) -> None:
        result = self.run_eval("--help")
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(b"", result.stderr)
        normalized = " ".join(result.stdout.decode().split())
        for fragment in (
            "usage: eval-teamwork.py",
            "--split {dev,release}",
            "--all",
            "--optimizer-ledger PATH",
            "Validate Teamwork eval fixtures.",
        ):
            self.assertIn(fragment, normalized)
        self.assertEqual(2, normalized.count("--split {dev,release}"))
        self.assertEqual(2, normalized.count("--optimizer-ledger PATH"))

    def test_case_outputs_keep_the_public_shape_without_freezing_case_data(self) -> None:
        selections = {
            ("--split", "dev"): "dev",
            ("--split", "release"): "release",
            ("--all",): "all",
        }
        for args, selection in selections.items():
            with self.subTest(args=args):
                result = self.run_eval(*args)
                self.assertEqual(0, result.returncode, result.stderr.decode())
                self.assertEqual(b"", result.stderr)
                lines = result.stdout.decode().splitlines()
                self.assertEqual(2, len(lines))
                summary = json.loads(lines[0])
                cases = selected_cases(selection)
                self.assertEqual("pass", summary["status"])
                self.assertEqual(selection, summary["selection"])
                self.assertEqual(len(cases), summary["cases"])
                self.assertEqual([case["id"] for case in cases], summary["case_ids"])
                self.assertTrue(lines[1].startswith(f"OK: Teamwork eval {selection} passed"))

    def test_optimizer_ledger_success_output_is_preserved(self) -> None:
        entry = {
            "date": "2026-07-15",
            "candidate_id": "compatibility_test",
            "kind": "skillopt-lite",
            "provider": "deterministic",
            "model": "stdlib",
            "model_config": "fixed",
            "prompt_or_template": "README.md",
            "owned_files": ["scripts/eval-teamwork.py"],
            "denylist": ["none"],
            "baseline": "README.md",
            "treatment": "README.md",
            "gate_decision": "accept",
            "rollback": "README.md",
            "validation": ["compatibility test"],
            "release_audit": "checked",
            "reviewer": "unittest",
            "decision": "accepted",
        }
        with tempfile.TemporaryDirectory() as temporary:
            ledger = Path(temporary) / "optimizer-candidates.jsonl"
            ledger.write_text(json.dumps(entry) + "\n", encoding="utf-8")
            result = self.run_eval("--optimizer-ledger", str(ledger))

        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(b"", result.stderr)
        self.assertEqual(
            b'{"rows": 1, "selection": "optimizer-ledger", "status": "pass"}\n'
            b"OK: optimizer ledger passed (1 rows)\n",
            result.stdout,
        )

    def test_accepted_ledger_reader_enforces_v2_no_downgrade(self) -> None:
        v2 = {
            "date": "2026-07-16",
            "schema_version": 2,
            "package_version": "3.4.0",
            "behavior_claims": [
                {
                    "type": "SOURCE_PARITY",
                    "evidence_lane": "STATIC_OFFLINE",
                    "claim_limits": ["Bounded to recorded source evidence."],
                    "provenance": {
                        "package_version": "3.4.0",
                        "source_sha256": "a" * 64,
                    },
                }
            ],
        }
        legacy = {"date": "2026-07-17"}
        with tempfile.TemporaryDirectory() as temporary:
            ledger = Path(temporary) / "accepted.jsonl"
            ledger.write_text(
                json.dumps(v2) + "\n" + json.dumps(legacy) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(EvalError, "must remain schema_version 2"):
                validate_ledger_lines(ledger, "accepted.jsonl", {"date"})


if __name__ == "__main__":
    unittest.main()
