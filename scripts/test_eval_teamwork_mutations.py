#!/usr/bin/env python3
"""Mutation tests for semantic routing pairs and topology ownership."""

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


class PairMutationTests(unittest.TestCase):
    def mutated_manifest(self) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, object]]:
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "pairs.json"
        value = json.loads((ROOT / "evals/teamwork/routing-pairs.json").read_text())
        return temporary, path, value

    def test_collapsing_pair_routes_is_rejected(self) -> None:
        temporary, path, value = self.mutated_manifest()
        with temporary:
            value["pairs"][0]["negative"]["expected_route"] = value["pairs"][0]["positive"]["expected_route"]
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(EvalError, "routes must differ"):
                validate_pair_manifest(path)

    def test_losing_positive_public_skill_coverage_is_rejected(self) -> None:
        temporary, path, value = self.mutated_manifest()
        with temporary:
            value["pairs"] = [
                pair for pair in value["pairs"]
                if pair["positive"]["expected_route"] != "teamwork-debug"
            ]
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(EvalError, "lack positive coverage"):
                validate_pair_manifest(path)

    def test_owner_must_be_active_topology_source(self) -> None:
        temporary, path, value = self.mutated_manifest()
        with temporary:
            value["pairs"][0]["owner"] = "skills/teamwork-explore/SKILL.md"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(EvalError, "not an active topology source"):
                validate_pair_manifest(path)

    def test_forbidden_collaborate_state_machine_is_rejected(self) -> None:
        source = (ROOT / "skills/teamwork-collaborate/SKILL.md").read_text()
        with self.assertRaisesRegex(EvalError, "L1/L2/L3"):
            validate_skill_source_contract(
                "teamwork-collaborate",
                source + "\nRuntime state L1 transitions to L2 and L3.\n",
            )

    def test_selected_cases_have_both_pair_polarities(self) -> None:
        by_pair: dict[str, set[str]] = {}
        for case in selected_cases("all"):
            by_pair.setdefault(case["pair_id"], set()).add(case["polarity"])
        self.assertTrue(by_pair)
        self.assertTrue(all(value == {"positive", "negative"} for value in by_pair.values()))


if __name__ == "__main__":
    unittest.main()
