#!/usr/bin/env python3
"""Mutation tests for the compact Teamwork v4 eval contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/eval-teamwork.py"
sys.path.insert(0, str(ROOT / "scripts"))

from teamwork_tooling.evaluation.cases import (  # noqa: E402
    _validate_coverage,
    load_json,
    selected_cases,
    validate_case,
    validate_ledger_lines,
    validate_rubrics,
)
from teamwork_tooling.evaluation.contracts import (  # noqa: E402
    CANONICAL_SKILL_COUNT,
    CASE_DIR,
    DEV_CAPABILITY_COVERAGE,
    EvalError,
    LEDGER_SCHEMAS,
    RELEASE_CAPABILITY_COVERAGE,
)
from teamwork_tooling.evaluation.sources import (  # noqa: E402
    SKILL_CONCEPTS,
    dependency_cycles,
    discover_skill_inventory,
    validate_semantic_sources,
    validate_skill_source_contract,
    validate_skill_topology,
)


class EvalCliTests(unittest.TestCase):
    def run_eval(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_dev_split_passes_and_is_nonempty(self) -> None:
        result = self.run_eval("--split", "dev")
        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout.splitlines()[0])
        self.assertGreater(summary["cases"], 0)
        self.assertEqual({"dev"}, set(summary["by_split"]))

    def test_release_split_passes_and_is_nonempty(self) -> None:
        result = self.run_eval("--split", "release")
        self.assertEqual(0, result.returncode, result.stderr)
        summary = json.loads(result.stdout.splitlines()[0])
        self.assertGreaterEqual(summary["cases"], len(RELEASE_CAPABILITY_COVERAGE))
        self.assertEqual({"release"}, set(summary["by_split"]))

    def test_release_split_contains_named_boundaries_by_capability(self) -> None:
        observed = {
            (
                case["expected"]["capability"],
                case["expected"]["scenario"],
                case["expected"]["language"],
            )
            for case in selected_cases("release")
        }
        self.assertTrue(RELEASE_CAPABILITY_COVERAGE.issubset(observed))


class TopologyMutationTests(unittest.TestCase):
    @staticmethod
    def write_inventory(root: Path) -> None:
        for skill in SKILL_CONCEPTS:
            directory = root / "skills" / skill
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text(
                f"---\nname: {skill}\ndescription: Use when testing {skill}.\n---\n",
                encoding="utf-8",
            )

    def test_repository_inventory_is_discovered_as_nine(self) -> None:
        inventory = discover_skill_inventory()
        self.assertEqual(CANONICAL_SKILL_COUNT, len(inventory))
        self.assertEqual(set(SKILL_CONCEPTS), set(inventory))

    def test_added_eleventh_skill_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_inventory(root)
            extra = root / "skills/teamwork-execute"
            extra.mkdir()
            (extra / "SKILL.md").write_text(
                "---\nname: teamwork-execute\ndescription: Use when testing.\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(EvalError, "must contain 10 skills"):
                validate_skill_topology(root)

    def test_router_name_is_rejected_even_if_count_stays_nine(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_inventory(root)
            removed = root / "skills/teamwork-update"
            (removed / "SKILL.md").unlink()
            removed.rmdir()
            router = root / "skills/using-teamwork"
            router.mkdir()
            (router / "SKILL.md").write_text(
                "---\nname: using-teamwork\ndescription: Use when routing.\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(EvalError, "retired skill remains"):
                validate_skill_topology(root)

    def test_behavior_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_inventory(root)
            reference = root / "skills/teamwork-design/references/options.md"
            reference.parent.mkdir()
            reference.write_text("hidden behavior\n", encoding="utf-8")
            with self.assertRaisesRegex(EvalError, "only the three named one-level advanced references are allowed"):
                validate_skill_topology(root)

    def test_skill_local_behavior_script_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_inventory(root)
            script = root / "skills/grill-me/scripts/state.py"
            script.parent.mkdir()
            script.write_text("pass\n", encoding="utf-8")
            with self.assertRaisesRegex(EvalError, "behavioral scripts are not allowed"):
                validate_skill_topology(root)

    def test_cross_skill_load_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_inventory(root)
            design = root / "skills/teamwork-design/SKILL.md"
            design.write_text(
                design.read_text(encoding="utf-8")
                + "Read `skills/teamwork-research/SKILL.md` before proceeding.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(EvalError, "must not load another Teamwork skill"):
                validate_skill_topology(root)

    def test_cycle_detector_is_mutation_sensitive(self) -> None:
        self.assertEqual([], dependency_cycles({"design": {"plan"}, "plan": set()}))
        cycles = dependency_cycles({"design": {"plan"}, "plan": {"design"}})
        self.assertEqual([["design", "plan", "design"]], cycles)


class SemanticSourceMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {
            skill: (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            for skill in SKILL_CONCEPTS
        }

    def test_repository_sources_satisfy_concept_contracts(self) -> None:
        validate_semantic_sources()

    def assert_concept_removal_rejected(self, skill: str, label: str) -> None:
        source = self.sources[skill]
        patterns = dict(SKILL_CONCEPTS[skill])[label]
        mutated = source
        for pattern in patterns:
            mutated = re.sub(pattern, "[removed]", mutated, flags=re.IGNORECASE | re.DOTALL)
        self.assertNotEqual(source, mutated, f"test could not locate {skill}/{label}")
        with self.assertRaisesRegex(EvalError, re.escape(label)):
            validate_skill_source_contract(skill, mutated)

    def test_research_external_trigger_is_protected(self) -> None:
        self.assert_concept_removal_rejected("teamwork-research", "external lookup trigger")

    def test_research_local_native_control_is_protected(self) -> None:
        self.assert_concept_removal_rejected("teamwork-research", "local evidence stays native")

    def test_research_citation_and_privacy_boundaries_are_protected(self) -> None:
        self.assert_concept_removal_rejected("teamwork-research", "citations")
        self.assert_concept_removal_rejected("teamwork-research", "privacy boundary")

    def test_research_rejects_local_activation_overlap(self) -> None:
        mutated = self.sources["teamwork-research"] + (
            "\nEnter Research for local repository code, configuration, tests, and logs.\n"
        )
        with self.assertRaisesRegex(EvalError, "local repository inspection activates Research"):
            validate_skill_source_contract("teamwork-research", mutated)

    def test_design_activation_and_tradeoff_boundaries_are_protected(self) -> None:
        self.assert_concept_removal_rejected("teamwork-design", "unresolved material choice trigger")
        self.assert_concept_removal_rejected("teamwork-design", "genuine alternatives only")

    def test_design_question_and_plan_boundaries_are_protected(self) -> None:
        self.assert_concept_removal_rejected("teamwork-design", "recommendation before question")
        self.assert_concept_removal_rejected("teamwork-design", "managed Design transaction")
        self.assert_concept_removal_rejected("teamwork-design", "Plan boundary")

    def test_plan_selected_direction_and_no_redesign_are_protected(self) -> None:
        self.assert_concept_removal_rejected("teamwork-plan", "selected direction prerequisite")
        self.assert_concept_removal_rejected("teamwork-plan", "no redesign or implementation")

    def test_plan_rejects_brainstorming_overlap(self) -> None:
        mutated = self.sources["teamwork-plan"] + "\nGenerate and compare three alternative options.\n"
        with self.assertRaisesRegex(EvalError, "Plan owns option discovery"):
            validate_skill_source_contract("teamwork-plan", mutated)

    def test_grill_ordinary_no_write_and_major_transaction_are_protected(self) -> None:
        self.assert_concept_removal_rejected("grill-me", "ordinary activation is no-write")
        self.assert_concept_removal_rejected("grill-me", "major change auto-transaction")

    def test_grill_transaction_writer_and_no_files_override_are_protected(self) -> None:
        self.assert_concept_removal_rejected("grill-me", "transaction-owned writer")
        self.assert_concept_removal_rejected("grill-me", "initialized writable prerequisite")
        self.assert_concept_removal_rejected("grill-me", "no-files override")

    def test_nonimplementation_boundary_is_protected_across_cognitive_skills(self) -> None:
        for skill, label in (
            ("teamwork-design", "read-only and no implementation"),
            ("teamwork-plan", "no redesign or implementation"),
            ("grill-me", "no implementation authority"),
        ):
            with self.subTest(skill=skill):
                self.assert_concept_removal_rejected(skill, label)

    def test_remaining_capability_owners_keep_their_distinct_contracts(self) -> None:
        for skill, label in (
            ("teamwork-debug", "same-path rerun"),
            ("teamwork-review", "read-only review"),
            ("teamwork-goal", "explicit modifier"),
            ("teamwork-init", "project-only ownership"),
            ("teamwork-update", "global-only ownership"),
        ):
            with self.subTest(skill=skill):
                self.assert_concept_removal_rejected(skill, label)


class CapabilityCaseMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rubrics = validate_rubrics()
        cls.cases = [load_json(path) for path in sorted(CASE_DIR.glob("*.v4.json"))]

    def validate_mutated_case(self, data: dict[str, object]) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / f"{data['id']}.{data['split']}.v4.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            validate_case(path, self.rubrics)

    def case(self, capability: str, scenario: str, language: str) -> dict[str, object]:
        for data in self.cases:
            expected = data["expected"]
            if (
                expected["capability"],
                expected["scenario"],
                expected["language"],
            ) == (capability, scenario, language):
                return copy.deepcopy(data)
        self.fail(f"missing fixture {capability}/{scenario}/{language}")

    def test_dev_coverage_is_mutation_sensitive_without_case_id_checks(self) -> None:
        key = ("design", "activation", "zh")
        mutated = [
            case
            for case in self.cases
            if (
                case["expected"]["capability"],
                case["expected"]["scenario"],
                case["expected"]["language"],
            ) != key
        ]
        self.assertIn(key, DEV_CAPABILITY_COVERAGE)
        with self.assertRaisesRegex(EvalError, "missing dev capability coverage"):
            _validate_coverage(mutated)

    def test_release_coverage_is_mutation_sensitive(self) -> None:
        key = ("grill", "persistence-boundary", "en")
        mutated = [
            case
            for case in self.cases
            if (
                case["expected"]["capability"],
                case["expected"]["scenario"],
                case["expected"]["language"],
            ) != key
        ]
        self.assertIn(key, RELEASE_CAPABILITY_COVERAGE)
        with self.assertRaisesRegex(EvalError, "missing release capability coverage"):
            _validate_coverage(mutated)

    def test_required_contract_token_removal_is_rejected(self) -> None:
        data = self.case("research", "external", "en")
        data["expected"]["requires"].remove("citations")
        with self.assertRaisesRegex(EvalError, "capability coverage missing: citations"):
            self.validate_mutated_case(data)

    def test_natural_question_first_cannot_smuggle_save_invocation(self) -> None:
        data = self.case("grill", "natural-question-first", "en")
        data["prompt"] += " $grill-me"
        with self.assertRaisesRegex(EvalError, "must not use \\$grill-me"):
            self.validate_mutated_case(data)

    def test_explicit_save_requires_explicit_skill_invocation(self) -> None:
        data = self.case("grill", "explicit-save", "en")
        data["prompt"] = "Save this discussion."
        with self.assertRaisesRegex(EvalError, "must explicitly invoke \\$grill-me"):
            self.validate_mutated_case(data)

    def test_no_implementation_needs_an_observable_negative_control(self) -> None:
        data = self.case("design", "activation", "en")
        data["must_not"] = ["change the topic"]
        with self.assertRaisesRegex(EvalError, "observable negative control"):
            self.validate_mutated_case(data)

    def test_privacy_case_requires_sensitive_data_negative_control(self) -> None:
        data = self.case("research", "privacy-boundary", "en")
        data["must_not"] = ["send unrelated values"]
        with self.assertRaisesRegex(EvalError, "sensitive-data negative control"):
            self.validate_mutated_case(data)

    def test_static_fixture_cannot_claim_live_evidence(self) -> None:
        data = self.case("native", "local-evidence", "en")
        data["evidence"] = "Observed live activation."
        with self.assertRaisesRegex(EvalError, "static-evidence limit"):
            self.validate_mutated_case(data)


class LedgerMutationTests(unittest.TestCase):
    def test_optimizer_ledger_rejects_placeholder_evidence(self) -> None:
        entry = {
            "date": "2026-07-19",
            "candidate_id": "v4_mutation",
            "kind": "skillopt-lite",
            "provider": "offline",
            "model": "deterministic",
            "model_config": "fixed",
            "prompt_or_template": "not_applicable",
            "owned_files": ["skills/teamwork-design/SKILL.md"],
            "denylist": ["evals/teamwork/cases/*.json"],
            "baseline": "README.md",
            "treatment": "README.md",
            "gate_decision": "reject",
            "rollback": "README.md",
            "validation": ["scripts/validate.sh"],
            "release_audit": "checked",
            "reviewer": "unittest",
            "decision": "rejected",
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "optimizer.jsonl"
            path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(EvalError, "prompt_or_template must not be"):
                validate_ledger_lines(
                    path,
                    "optimizer-candidates.jsonl",
                    LEDGER_SCHEMAS["optimizer-candidates.jsonl"],
                )


if __name__ == "__main__":
    unittest.main()
