#!/usr/bin/env python3
"""Mutation checks for the capability-first static question fixtures."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval-teamwork.py"
OUTPUT = ROOT / "evals" / "teamwork" / "outputs" / "question-first" / "dev.jsonl"

SPEC = importlib.util.spec_from_file_location("eval_teamwork", SCRIPT)
assert SPEC and SPEC.loader
EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVAL)


class StaticOutputMutationTests(unittest.TestCase):
    def mutate_row(self, case_id: str, mutate) -> subprocess.CompletedProcess[str]:
        rows = [json.loads(line) for line in OUTPUT.read_text(encoding="utf-8").splitlines()]
        row = next(item for item in rows if item["case_id"] == case_id)
        mutate(row)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "question-first"
            target.mkdir(parents=True)
            (target / "dev.jsonl").write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in rows) + "\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["TEAMWORK_EVAL_OUTPUT_DIR"] = str(root)
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--split", "dev"],
                text=True,
                capture_output=True,
                check=False,
                env=env,
                cwd=ROOT,
            )

    def assert_rejected(self, result: subprocess.CompletedProcess[str], text: str) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(text, result.stderr)

    @staticmethod
    def set_last_output(row: dict, text: str) -> None:
        row["trajectory"][-1]["assistant"] = text
        row["output"] = text

    def test_legacy_packet_marker_is_rejected(self) -> None:
        def mutate(row: dict) -> None:
            text = "Grill status: active\n" + row["trajectory"][0]["assistant"]
            row["trajectory"][0]["assistant"] = text
            row["output"] = text

        self.assert_rejected(
            self.mutate_row("grill-rename-ownership-contrast", mutate),
            "superseded grill packet/state protocol",
        )

    def test_question_annotation_must_match_visible_question(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][0]["asked_candidates"] = []

        self.assert_rejected(
            self.mutate_row("grill-rename-ownership-contrast", mutate),
            "question text and asked_candidates annotation disagree",
        )

    def test_semantic_oracle_rejects_agent_owned_question(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][0]["asked_candidates"] = ["private_symbol_rename"]

        self.assert_rejected(
            self.mutate_row("grill-rename-ownership-contrast", mutate),
            "do not match semantic oracle",
        )

    def test_one_decision_per_turn_is_enforced_without_a_global_quota(self) -> None:
        def mutate(row: dict) -> None:
            text = row["output"] + " Should the alias last two releases?"
            self.set_last_output(row, text)

        self.assert_rejected(
            self.mutate_row("grill-rename-ownership-contrast", mutate),
            "asks more than one decision",
        )

    def test_zero_question_case_cannot_manufacture_a_question(self) -> None:
        def mutate(row: dict) -> None:
            self.set_last_output(row, row["output"] + " Should we ask anyway?")

        self.assert_rejected(
            self.mutate_row("grill-zero-question-low-value", mutate),
            "question text and asked_candidates annotation disagree",
        )

    def test_question_first_fixture_cannot_enact_work(self) -> None:
        def mutate(row: dict) -> None:
            self.set_last_output(row, row["output"] + " I will implement it now.")

        self.assert_rejected(
            self.mutate_row("grill-rename-ownership-contrast", mutate),
            "enacts work inside the question-first fixture",
        )

    def test_completion_cannot_invent_implementation_authority(self) -> None:
        def mutate(row: dict) -> None:
            self.set_last_output(row, row["output"] + " Implementation authority is granted.")

        self.assert_rejected(
            self.mutate_row("grill-zero-question-low-value", mutate),
            "invents implementation authority",
        )

    def test_ordinary_question_rejects_choice_card_ceremony(self) -> None:
        def mutate(row: dict) -> None:
            self.set_last_output(row, row["output"] + "\nOptions:\n- Keep alias\n- Break scripts")

        self.assert_rejected(
            self.mutate_row("ordinary-material-clarification-control", mutate),
            "must be one concise question, not a choice card",
        )

    def test_ordinary_question_must_target_public_cli_compatibility(self) -> None:
        def mutate(row: dict) -> None:
            self.set_last_output(row, "Should the helper use Python?")

        self.assert_rejected(
            self.mutate_row("ordinary-material-clarification-control", mutate),
            "must ask the public CLI compatibility question",
        )

    def test_lightweight_control_rejects_question_and_code_toolchain(self) -> None:
        def question(row: dict) -> None:
            self.set_last_output(row, "Should I fix the typo?")

        self.assert_rejected(
            self.mutate_row("question-first-lightweight-control", question),
            "must not use grill ceremony",
        )

        def toolchain(row: dict) -> None:
            self.set_last_output(row, "I will use a shell directly for the typo fix.")

        self.assert_rejected(
            self.mutate_row("question-first-lightweight-control", toolchain),
            "must not plan or dispatch",
        )

    def test_authored_fixture_cannot_claim_live_model_evidence(self) -> None:
        def mutate(row: dict) -> None:
            row["evidence_tier"] = "live-verified"

        self.assert_rejected(
            self.mutate_row("grill-rename-ownership-contrast", mutate),
            "it is not live model evidence",
        )


class CaseSchemaMutationTests(unittest.TestCase):
    def load_case(self, name: str) -> dict:
        return json.loads(
            (ROOT / "evals" / "teamwork" / "cases" / name).read_text(encoding="utf-8")
        )

    def validate(self, data: dict) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / f"{data['id']}.dev.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            EVAL.validate_case(
                path,
                {"assistance-quality", "behavioral-contracts"},
            )

    def test_expected_question_must_be_user_owned(self) -> None:
        data = self.load_case("grill-rename-ownership-contrast.dev.json")
        data["expected_asked_candidates"] = ["private_symbol_rename"]
        with self.assertRaisesRegex(EVAL.EvalError, "expected question is not user-owned"):
            self.validate(data)

    def test_retired_protocol_fields_are_rejected(self) -> None:
        for field, value in (
            ("expected_question_ids", ["public_cli_rename"]),
            ("blocked_route", "plan"),
            ("expected_close", {"format": "concise"}),
        ):
            with self.subTest(field=field):
                data = self.load_case("grill-rename-ownership-contrast.dev.json")
                data[field] = value
                with self.assertRaisesRegex(EVAL.EvalError, "retired grill protocol fields"):
                    self.validate(data)

    def test_internal_oracle_has_no_fixed_three_decision_ceiling(self) -> None:
        data = self.load_case("grill-rename-ownership-contrast.dev.json")
        for index in range(2, 5):
            candidate = f"public_choice_{index}"
            data["candidates"].append(
                {
                    "candidate_id": candidate,
                    "owner": "user-decision",
                    "grounding_required": True,
                    "expected_action": "ask",
                }
            )
            data["expected_asked_candidates"].append(candidate)
        self.validate(data)

    def test_ask_predicate_case_rejects_missing_coverage(self) -> None:
        data = self.load_case("review-bounded-recheck.dev.json")
        data["expected"]["requires"].remove("one_corrective_recheck")
        with self.assertRaisesRegex(EVAL.EvalError, "ask-predicate coverage missing"):
            self.validate(data)

    def test_ask_predicate_case_rejects_retired_lifecycle_terms(self) -> None:
        data = self.load_case("goal-dependent-branch-retry.dev.json")
        data["must"].append("Preserve the " + "Task Contract between attempts.")
        with self.assertRaisesRegex(EVAL.EvalError, "retired lifecycle term remains"):
            self.validate(data)

    def test_review_case_locks_stable_ids_blockers_and_one_recheck(self) -> None:
        data = self.load_case("review-bounded-recheck.dev.json")
        self.assertEqual(
            set(data["expected"]["requires"]),
            {"stable_finding_ids", "review_taxonomy", "blocker_classification", "risk_gated_fresh_review", "one_corrective_recheck"},
        )
        self.validate(data)

    def test_working_facts_case_rejects_missing_dependency_behavior(self) -> None:
        data = self.load_case("working-facts-scope-correction.dev.json")
        data["expected"]["requires"].remove("stale_delegated_results_discarded")
        with self.assertRaisesRegex(EVAL.EvalError, "Working Facts coverage missing"):
            self.validate(data)

    def test_minimality_case_rejects_missing_coverage(self) -> None:
        data = self.load_case("minimality-justified-surface.dev.json")
        data["expected"]["requires"].remove("no_code_golf")
        with self.assertRaisesRegex(EVAL.EvalError, "minimality coverage missing"):
                self.validate(data)


    def test_active_case_rejects_retired_stage_card_language(self) -> None:
        data = self.load_case("working-facts-scope-correction.dev.json")
        data["must"].append("Restore the " + "Stage Entry Card before continuing.")
        with self.assertRaisesRegex(EVAL.EvalError, "retired workflow term remains"):
            self.validate(data)

    def test_update_refresh_case_locks_target_and_route(self) -> None:
        for field, value, error in (
            ("target", "AGENTS.md", "target must be skills/teamwork-update/SKILL.md"),
            ("route", "project-maintainer", "route must be update"),
        ):
            with self.subTest(field=field):
                data = self.load_case("update-user-refresh.dev.json")
                if field == "target":
                    data[field] = value
                else:
                    data["expected"][field] = value
                with self.assertRaisesRegex(EVAL.EvalError, error):
                    self.validate(data)

    def test_maintainer_release_case_locks_target_and_route(self) -> None:
        for field, value, error in (
            ("target", "skills/teamwork-update/SKILL.md", "target must be AGENTS.md"),
            ("route", "update", "route must be project-maintainer"),
        ):
            with self.subTest(field=field):
                data = self.load_case("update-release-ledger.release.json")
                if field == "target":
                    data[field] = value
                else:
                    data["expected"][field] = value
                with self.assertRaisesRegex(EVAL.EvalError, error):
                    self.validate(data)

    def test_discussion_case_rejects_missing_contract_coverage(self) -> None:
        data = self.load_case("discussion-authorized-checkpoint.dev.json")
        data["expected"]["requires"].remove("material_checkpoint_only")
        with self.assertRaisesRegex(EVAL.EvalError, "discussion coverage missing"):
            self.validate(data)


class SemanticSourceMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.review = (ROOT / "skills/teamwork-review/SKILL.md").read_text(encoding="utf-8")
        cls.goal = (ROOT / "skills/teamwork-goal/SKILL.md").read_text(encoding="utf-8")
        cls.role_playbook = (
            ROOT / "skills/using-teamwork/references/role-playbook.md"
        ).read_text(encoding="utf-8")
        cls.workflow_contract = (
            ROOT / "skills/using-teamwork/references/workflow-contract.md"
        ).read_text(encoding="utf-8")
        cls.review_lenses = (
            ROOT / "skills/using-teamwork/references/review-lenses.md"
        ).read_text(encoding="utf-8")
        cls.project_init = (
            ROOT / "skills/using-teamwork/references/project-init.md"
        ).read_text(encoding="utf-8")
        cls.agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cls.check_update = (
            ROOT / "skills/using-teamwork/references/check-update.md"
        ).read_text(encoding="utf-8")
        cls.codex = (ROOT / "CODEX.md").read_text(encoding="utf-8")
        cls.discussion_template = (
            ROOT / "skills/using-teamwork/references/teamwork-discussion-template.md"
        ).read_text(encoding="utf-8")
        cls.skill_sources = {
            skill: (ROOT / path).read_text(encoding="utf-8")
            for skill, (path, _) in EVAL.SKILL_SOURCE_CONTRACTS.items()
        }

    def assert_skill_contract_rejected(
        self, skill: str, old: str, new: str, error: str
    ) -> None:
        source = self.skill_sources[skill]
        mutated = source.replace(old, new)
        self.assertNotEqual(mutated, source, f"mutation did not change {skill}")
        with self.assertRaisesRegex(EVAL.EvalError, error):
            EVAL.validate_skill_source_contract(skill, mutated)

    def assert_mainline_focus_rejected(
        self, source_name: str, old: str, new: str, error: str
    ) -> None:
        sources = {
            "grill": self.skill_sources["grill-me"],
            "project_init": self.project_init,
            "teamwork_init": self.skill_sources["teamwork-init"],
        }
        mutated = sources[source_name].replace(old, new)
        self.assertNotEqual(mutated, sources[source_name], f"mutation did not change {source_name}")
        sources[source_name] = mutated
        with self.assertRaisesRegex(EVAL.EvalError, error):
            EVAL.validate_mainline_focus_source_text(
                sources["grill"],
                sources["project_init"],
                sources["teamwork_init"],
            )

    def test_rejects_retired_review_severity_taxonomy(self) -> None:
        mutated = self.review.replace(
            "one class: `BLOCKER`, `FOLLOW-UP`, or `SUGGESTION`",
            "one class: `blocker`, `major`, or `minor`",
        )
        with self.assertRaisesRegex(EVAL.EvalError, "review taxonomy must be"):
            EVAL.validate_semantic_source_text(mutated, self.goal, self.role_playbook)

    def test_rejects_retired_role_playbook_severity_taxonomy(self) -> None:
        mutated = self.role_playbook.replace(
            "`BLOCKER | FOLLOW-UP | SUGGESTION` findings",
            "`blocker | major | minor` findings",
        )
        with self.assertRaisesRegex(EVAL.EvalError, "role-playbook.md: review taxonomy must be"):
            EVAL.validate_semantic_source_text(self.review, self.goal, mutated)

    def test_rejects_goal_activation_merely_when_available(self) -> None:
        mutated = self.goal.replace(
            "only when the user explicitly requests Goal mode or\naccepts a Goal Proposal",
            "when available",
        )
        with self.assertRaisesRegex(EVAL.EvalError, "explicit user request or accepted Goal Proposal"):
            EVAL.validate_semantic_source_text(self.review, mutated, self.role_playbook)

    def test_goal_rejects_discarded_retry_invariants(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-goal",
            "identify the preserved scope/invariants, failed claim and\nstage, prior evidence, do-not-repeat constraints",
            "discard accepted scope and retry from scratch",
            "preserved Goal Invariants",
        )

    def test_goal_rejects_unchanged_no_progress_retry(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-goal",
            "Stop on repeated no-progress without an evidence-backed strategy delta",
            "Repeat the same attempt after no progress",
            "strategy delta",
        )

    def test_using_teamwork_rejects_removed_native_fast_path(self) -> None:
        self.assert_skill_contract_rejected(
            "using-teamwork",
            "Small,\nclear tasks stay native",
            "All tasks enter a Teamwork stage",
            "Native fast path",
        )

    def test_grill_rejects_removed_explicit_activation(self) -> None:
        self.assert_skill_contract_rejected(
            "grill-me",
            "Enter for an explicit request",
            "Enter whenever available",
            "explicit activation",
        )

    def test_research_rejects_collapsed_evidence_tiers(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-research",
            "`observed`, `inferred`,\nand `claimed` findings",
            "`claimed` findings",
            "observed/inferred/claimed evidence",
        )

    def test_debug_rejects_removed_discriminating_hypotheses(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-debug",
            "name discriminating evidence",
            "collect any evidence",
            "discriminating hypotheses",
        )

    def test_plan_rejects_optional_non_simple_grill(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-plan",
            "Every non-simple Plan enters evidence-first `grill-me`",
            "A non-simple Plan may enter `grill-me`",
            "non-simple material Grill",
        )

    def test_execute_rejects_reset_failed_ac_evidence(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-execute",
            "Failed AC evidence stays failed until direct evidence changes that AC",
            "Failed AC evidence resets after any edit",
            "failed-AC monotonicity",
        )

    def test_init_rejects_global_failure_hard_gate(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-init",
            "Project surfaces continue even when the global install returns an actionable configuration failure",
            "Project surfaces stop when the global install returns an actionable configuration failure",
            "safe local continuation",
        )

    def test_update_rejects_release_metadata_scope(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-update",
            "Never edit `VERSION`, plugin manifests, changelogs, release commits, tags, or\n  GitHub Releases",
            "Edit VERSION and publish a GitHub Release",
            "no release metadata",
        )

    def test_update_rejects_ignored_project_surfaces(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-update",
            "refresh all global skills, agents, managed policy,\n   routing, and applicable project surfaces",
            "refresh global skills and ignore project surfaces",
            "global and project refresh",
        )

    def test_update_rejects_additive_publication_authority(self) -> None:
        mutated = self.skill_sources["teamwork-update"] + (
            "\nWith explicit publication authority, edit VERSION and plugin manifests, "
            "write the changelogs and release commit, create the tag, and publish the "
            "GitHub Release.\n"
        )
        with self.assertRaisesRegex(EVAL.EvalError, "must not authorize maintainer publication"):
            EVAL.validate_release_boundary_source_text(
                mutated,
                self.skill_sources["using-teamwork"],
                self.check_update,
                self.codex,
                False,
            )

    def test_release_policy_rejects_duplication_outside_agents(self) -> None:
        mutated_codex = self.codex + "\nOne release unit contains VERSION and tags.\n"
        with self.assertRaisesRegex(EVAL.EvalError, "must live only in root AGENTS.md"):
            EVAL.validate_release_boundary_source_text(
                self.skill_sources["teamwork-update"],
                self.skill_sources["using-teamwork"],
                self.check_update,
                mutated_codex,
                False,
            )

    def test_release_policy_rejects_restored_changelog_guide(self) -> None:
        with self.assertRaisesRegex(EVAL.EvalError, "changelog-guide.md"):
            EVAL.validate_release_boundary_source_text(
                self.skill_sources["teamwork-update"],
                self.skill_sources["using-teamwork"],
                self.check_update,
                self.codex,
                True,
            )

    def test_maintainer_release_rejects_engineering_only_changelog(self) -> None:
        mutated = self.agents.replace(
            "Write changelogs for users, not maintainers",
            "Write changelogs as internal engineering reports",
        )
        self.assertNotEqual(mutated, self.agents)
        with self.assertRaisesRegex(EVAL.EvalError, "user-facing changelog"):
            EVAL.validate_maintainer_release_source_text(mutated)

    def test_maintainer_release_rejects_partial_release_unit(self) -> None:
        mutated = self.agents.replace(
            "One release unit contains `VERSION`, both plugin manifests, both changelogs",
            "One release unit contains VERSION only",
        )
        self.assertNotEqual(mutated, self.agents)
        with self.assertRaisesRegex(EVAL.EvalError, "complete release unit"):
            EVAL.validate_maintainer_release_source_text(mutated)

    def test_rejects_removed_or_inverted_minimality_boundaries(self) -> None:
        mutations = (
            (
                self.workflow_contract.replace(
                    "the canonical owner/pattern,", "a new wrapper,"
                ),
                "canonical owner/pattern",
            ),
            (
                self.workflow_contract.replace(
                    "not fewer lines or files", "only fewer lines and files"
                ),
                "not fewer lines or files",
            ),
        )
        for workflow_contract, error in mutations:
            with self.subTest(error=error):
                with self.assertRaisesRegex(EVAL.EvalError, error):
                    EVAL.validate_minimality_source_text(
                        workflow_contract, self.review_lenses
                    )

    def test_grill_rejects_lost_mainline(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "Hold one mainline: the global goal, current focus, and why the next question\n  can change the project-level decision.",
            "Follow the latest local topic.",
            "hold one mainline",
        )

    def test_grill_rejects_irrelevant_questions(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "Every question must materially advance the mainline;\ndrop locally interesting details that no longer serve it.",
            "Ask any locally interesting question.",
            "materially advance the mainline",
        )

    def test_grill_rejects_per_turn_mainline_ribbon(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "restate that link briefly before asking; do not repeat it every turn.",
            "repeat that link on every turn.",
            "do not repeat it every turn",
        )

    def test_init_rejects_deterministic_bootstrap_as_explicit_default(self) -> None:
        self.assert_mainline_focus_rejected(
            "teamwork_init",
            "Explicit `teamwork-init` defaults to **Semantic init** unless the user asks only\nfor audit or deterministic bootstrap.",
            "Explicit teamwork-init defaults to deterministic bootstrap.",
            "defaults to",
        )

    def test_init_rejects_missing_primary_owner(self) -> None:
        self.assert_mainline_focus_rejected(
            "project_init",
            "Give every rule or\nfact one primary owner; other surfaces link to it or contain only a real delta.",
            "Duplicate every rule across instruction surfaces.",
            "one primary owner",
        )

    def test_init_rejects_meaningless_second_semantic_write(self) -> None:
        self.assert_mainline_focus_rejected(
            "project_init",
            "An equivalent second semantic audit with no new evidence, classification, or\nmainline change writes nothing and reports `no-change`.",
            "An equivalent second semantic audit rewrites the files.",
            "writes nothing",
        )

    def test_discussion_source_rejects_plural_path(self) -> None:
        protocol = (
            ROOT / "skills/using-teamwork/references/artifact-protocol.md"
        ).read_text(encoding="utf-8")
        mutated = protocol.replace(
            "docs/teamwork/discussion/", "docs/teamwork/discussions/"
        )
        self.assertNotEqual(mutated, protocol)
        with self.assertRaisesRegex(EVAL.EvalError, "singular discussion path"):
            EVAL.validate_discussion_source_text(
                self.skill_sources["grill-me"],
                self.skill_sources["using-teamwork"],
                mutated,
                self.discussion_template,
            )

    def test_discussion_source_rejects_retired_identity_or_authority(self) -> None:
        protocol = (
            ROOT / "skills/using-teamwork/references/artifact-protocol.md"
        ).read_text(encoding="utf-8")
        mutations = (
            (
                protocol.replace(
                    "it is not a transcript, a new skill, stage,\nroute, mode, state machine, or source of execution authority",
                    "it is a transcript, stage, route, mode, state machine, and source of execution authority",
                ),
                "supporting-only boundary",
            ),
            (
                protocol.replace("Do not update per turn.", "Update per turn."),
                "material-checkpoint updates",
            ),
            (
                protocol.replace(
                    "stays subordinate to\ncanonical project sources. It cannot promote itself or authorize execution",
                    "is canonical project memory and authorizes execution",
                ),
                "canonical and execution authority boundary",
            ),
        )
        for mutated, error in mutations:
            with self.subTest(error=error):
                self.assertNotEqual(mutated, protocol)
                with self.assertRaisesRegex(EVAL.EvalError, error):
                    EVAL.validate_discussion_source_text(
                        self.skill_sources["grill-me"],
                        self.skill_sources["using-teamwork"],
                        mutated,
                        self.discussion_template,
                    )

    def test_discussion_template_rejects_missing_required_sections(self) -> None:
        for heading, error in (
            ("## Route Map", "Route Map"),
            ("## Playback", "Playback"),
        ):
            with self.subTest(heading=heading):
                mutated = self.discussion_template.replace(heading, f"## Removed {heading}")
                with self.assertRaisesRegex(EVAL.EvalError, error):
                    EVAL.validate_discussion_template_text(mutated)

    def test_discussion_template_requires_supporting_authority(self) -> None:
        mutated = self.discussion_template.replace(
            "Authority: supporting", "Authority: canonical"
        )
        with self.assertRaisesRegex(EVAL.EvalError, "Authority: supporting"):
            EVAL.validate_discussion_template_text(mutated)

    def test_discussion_template_requires_textual_node_status(self) -> None:
        mutated = self.discussion_template.replace(
            'R2["R2 · Option A · open"]', 'R2["R2 · Option A"]'
        )
        with self.assertRaisesRegex(EVAL.EvalError, "textual status"):
            EVAL.validate_discussion_template_text(mutated)

    def test_discussion_template_rejects_map_note_status_mismatch(self) -> None:
        mutated = self.discussion_template.replace("- Status: open", "- Status: accepted", 1)
        self.assertNotEqual(mutated, self.discussion_template)
        with self.assertRaisesRegex(EVAL.EvalError, "status mismatch for R2"):
            EVAL.validate_discussion_template_text(mutated)

    def test_discussion_template_rejects_mismatched_or_dangling_keys(self) -> None:
        mutations = (
            self.discussion_template.replace(
                "### R1 — <short label>", "### R4 — <short label>"
            ),
            self.discussion_template.replace(
                '    R1 --> R3', '    R4["R4 · Extra · open"]\n    R1 --> R3'
            ),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated[-80:]):
                with self.assertRaisesRegex(EVAL.EvalError, "Route Map/Route Notes keys"):
                    EVAL.validate_discussion_template_text(mutated)

    def test_discussion_template_rejects_undefined_edge_key(self) -> None:
        mutated = self.discussion_template.replace("R1 --> R3", "R1 --> R4")
        self.assertNotEqual(mutated, self.discussion_template)
        with self.assertRaisesRegex(EVAL.EvalError, "undefined node keys: R4"):
            EVAL.validate_discussion_template_text(mutated)

    def test_discussion_template_rejects_note_details_in_diagram_labels(self) -> None:
        for field in ("Evidence", "Reason", "Mainline impact"):
            with self.subTest(field=field):
                mutated = self.discussion_template.replace(
                    'R2["R2 · Option A · open"]',
                    f'R2["R2 · Option A · open · {field}: benchmark"]',
                )
                with self.assertRaisesRegex(EVAL.EvalError, "diagram labels must not carry"):
                    EVAL.validate_discussion_template_text(mutated)

    def test_discussion_template_requires_every_route_note_field(self) -> None:
        mutated = self.discussion_template.replace(
            "- Reason: <why this option remains open>",
            "- Rationale omitted: <why this option remains open>",
        )
        with self.assertRaisesRegex(EVAL.EvalError, "Route Note R2 must include Reason"):
            EVAL.validate_discussion_template_text(mutated)

    def test_discussion_handoff_rejects_repeated_answered_decision(self) -> None:
        path = ROOT / "evals/teamwork/cases/discussion-handoff-playback.dev.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["trajectory"][0]["assistant"] = (
            "Playback: We already decided to use a dedicated discussion artifact and "
            "persist only long or materially branching Grill.\n"
            "Current: The route is restored.\nOpen: one decision remains.\n"
            "Next: Should we use a dedicated discussion artifact?"
        )
        with self.assertRaisesRegex(EVAL.EvalError, "repeats answered decision"):
            EVAL.validate_discussion_handoff_case(data, path)



if __name__ == "__main__":
    unittest.main()
