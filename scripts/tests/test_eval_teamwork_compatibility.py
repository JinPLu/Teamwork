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

from teamwork_tooling.evaluation.cases import selected_cases


class EvalTeamworkCompatibilityTests(unittest.TestCase):
    def run_eval(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )

    def test_help_output_remains_byte_compatible(self) -> None:
        result = self.run_eval("--help")
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(b"", result.stderr)
        self.assertEqual(
            "52028a236bba03efb6d76c86747c1f01dd74c17e26ae79b2731342a6b50bc953",
            hashlib.sha256(result.stdout).hexdigest(),
        )

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


if __name__ == "__main__":
    unittest.main()
