#!/usr/bin/env python3
"""Current public CLI checks for the deterministic Teamwork eval."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/eval-teamwork.py"
sys.path.insert(0, str(SCRIPT.parent))

from teamwork_tooling.evaluation.cases import selected_cases  # noqa: E402


class EvalTeamworkCliTests(unittest.TestCase):
    def run_eval(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )

    def test_help_lists_the_current_interface(self) -> None:
        result = self.run_eval("--help")
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(b"", result.stderr)
        normalized = " ".join(result.stdout.decode().split())
        for fragment in (
            "usage: eval-teamwork.py",
            "--split {dev,release}",
            "--all",
            "Validate Teamwork structural fixtures and routing pairs.",
        ):
            self.assertIn(fragment, normalized)

    def test_case_outputs_follow_the_current_shape(self) -> None:
        selections = {
            ("--split", "dev"): "dev",
            ("--split", "release"): "release",
            ("--all",): "all",
        }
        for args, selection in selections.items():
            with self.subTest(args=args):
                result = self.run_eval(*args)
                self.assertEqual(0, result.returncode, result.stderr.decode())
                lines = result.stdout.decode().splitlines()
                summary = json.loads(lines[0])
                cases = selected_cases(selection)
                self.assertEqual("pass", summary["status"])
                self.assertEqual(selection, summary["selection"])
                self.assertEqual(len(cases), summary["cases"])
                self.assertEqual([case["id"] for case in cases], summary["case_ids"])
                self.assertTrue(lines[1].startswith(f"OK: Teamwork eval {selection} passed"))

if __name__ == "__main__":
    unittest.main()
