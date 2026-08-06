#!/usr/bin/env python3
"""Mutation tests for semantic routing scenarios and topology ownership."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/eval-teamwork.py"
sys.path.insert(0, str(ROOT / "scripts"))

from teamwork_tooling.evaluation.cases import selected_cases, validate_pair_manifest  # noqa: E402
from teamwork_tooling.evaluation.contracts import EvalError  # noqa: E402
from teamwork_tooling.evaluation.sources import validate_skill_source_contract  # noqa: E402
from teamwork_tooling.topology import public_skill_paths  # noqa: E402


class EvalCliTests(unittest.TestCase):
    def test_each_split_is_nonempty(self) -> None:
        for split in ("dev", "release"):
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--split", split],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            summary = json.loads(result.stdout.splitlines()[0])
            self.assertGreater(summary["cases"], 0)


class ScenarioMutationTests(unittest.TestCase):
    def mutated_manifest(self) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, object]]:
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "scenarios.json"
        value = json.loads((ROOT / "evals/teamwork/routing-pairs.json").read_text())
        return temporary, path, value

    def test_unknown_route_is_rejected(self) -> None:
        temporary, path, value = self.mutated_manifest()
        with temporary:
            value["scenarios"][0]["expected_route"] = "teamwork-retired"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(EvalError, "expected route is not current"):
                validate_pair_manifest(path)

    def test_losing_changed_route_coverage_is_rejected(self) -> None:
        temporary, path, value = self.mutated_manifest()
        with temporary:
            value["scenarios"] = [
                scenario for scenario in value["scenarios"]
                if scenario["expected_route"] != "teamwork-debug"
            ]
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(EvalError, "do not cover changed/reasserted routes"):
                validate_pair_manifest(path)

    def test_owner_must_be_active_topology_source(self) -> None:
        temporary, path, value = self.mutated_manifest()
        with temporary:
            value["scenarios"][0]["owner"] = "skills/teamwork-explore/SKILL.md"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(EvalError, "not a current canonical source"):
                validate_pair_manifest(path)

    def test_forbidden_collaborate_state_machine_is_rejected(self) -> None:
        source = (ROOT / "skills/teamwork-collaborate/SKILL.md").read_text()
        with self.assertRaisesRegex(EvalError, "L1/L2/L3"):
            validate_skill_source_contract(
                "teamwork-collaborate",
                source + "\nRuntime state L1 transitions to L2 and L3.\n",
            )

    def test_selected_cases_cover_current_routes_without_pair_fields(self) -> None:
        cases = selected_cases("all")
        self.assertTrue(cases)
        self.assertEqual(
            {"native", *public_skill_paths(ROOT)},
            {case["expected"]["route"] for case in cases},
        )
        self.assertTrue(all("pair_id" not in case and "polarity" not in case for case in cases))


if __name__ == "__main__":
    unittest.main()
