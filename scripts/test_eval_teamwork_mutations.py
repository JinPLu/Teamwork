#!/usr/bin/env python3
"""Mutation checks for the capability-first static question fixtures."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from teamwork_tooling.evaluation.cases import (
    validate_case,
    validate_discussion_handoff_case,
)
from teamwork_tooling.evaluation.contracts import (
    EvalError,
    REQUIRED_ACTIVATION_CASES,
    SKILL_SOURCE_CONTRACTS,
)
from teamwork_tooling.evaluation.sources import (
    validate_always_loaded_policy_text,
    validate_audience_source_text,
    validate_decision_checkpoint_source_text,
    validate_discussion_source_text,
    validate_discussion_template_text,
    validate_mainline_focus_source_text,
    validate_maintainer_release_source_text,
    validate_minimal_handoff_source_text,
    validate_minimality_source_text,
    validate_outcome_first_source_parity,
    validate_release_boundary_source_text,
    validate_rule_maintenance_source_text,
    validate_semantic_source_text,
    validate_skill_source_contract,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval-teamwork.py"
OUTPUT = ROOT / "evals" / "teamwork" / "outputs" / "question-first" / "dev.jsonl"


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

    def test_mainline_distraction_cannot_replace_the_public_question(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][0]["assistant"] = (
                "Should we use JSON or YAML for the route label?"
            )

        self.assert_rejected(
            self.mutate_row("grill-question-value-stop", mutate),
            "does not preserve mainline_anchor",
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
            validate_case(
                path,
                {"assistance-quality", "behavioral-contracts"},
            )

    def test_expected_question_must_be_user_owned(self) -> None:
        data = self.load_case("grill-rename-ownership-contrast.dev.json")
        data["expected_asked_candidates"] = ["private_symbol_rename"]
        with self.assertRaisesRegex(EvalError, "expected question is not user-owned"):
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
                with self.assertRaisesRegex(EvalError, "retired grill protocol fields"):
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
        with self.assertRaisesRegex(EvalError, "ask-predicate coverage missing"):
            self.validate(data)

    def test_ask_predicate_case_rejects_retired_lifecycle_terms(self) -> None:
        data = self.load_case("goal-dependent-branch-retry.dev.json")
        data["must"].append("Preserve the " + "Task Contract between attempts.")
        with self.assertRaisesRegex(EvalError, "retired lifecycle term remains"):
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
        with self.assertRaisesRegex(EvalError, "Working Facts coverage missing"):
            self.validate(data)

    def test_minimality_case_rejects_missing_coverage(self) -> None:
        data = self.load_case("minimality-justified-surface.dev.json")
        data["expected"]["requires"].remove("no_code_golf")
        with self.assertRaisesRegex(EvalError, "minimality coverage missing"):
                self.validate(data)

    def test_weak_cue_matrix_has_bilingual_skills_and_native_controls(self) -> None:
        self.assertEqual(len(REQUIRED_ACTIVATION_CASES), 22)
        languages = {
            case_id.rsplit("-", 1)[-1] for case_id in REQUIRED_ACTIVATION_CASES
        }
        self.assertEqual(languages, {"en", "zh"})
        routes = {route for _, route, _, _ in REQUIRED_ACTIVATION_CASES.values()}
        self.assertEqual(
            routes,
            {
                "native", "router", "research", "debug", "plan", "grill",
                "execute", "review", "goal", "init", "update",
            },
        )
        route_languages: dict[str, set[str]] = {}
        for language, route, _, _ in REQUIRED_ACTIVATION_CASES.values():
            route_languages.setdefault(route, set()).add(language)
        self.assertTrue(
            all(languages == {"en", "zh"} for languages in route_languages.values())
        )

    def test_weak_cue_case_rejects_route_or_observable_drift(self) -> None:
        data = self.load_case("activation-debug-zh.dev.json")
        data["expected"]["route"] = "execute"
        with self.assertRaisesRegex(EvalError, "weak-cue route must be debug"):
            self.validate(data)
        data = self.load_case("activation-debug-zh.dev.json")
        data["expected"]["observable"] = "patch_applied"
        with self.assertRaisesRegex(
            EvalError, "weak-cue observable must be repro_before_fix"
        ):
            self.validate(data)

    def test_weak_cue_case_rejects_stage_name_in_prompt(self) -> None:
        data = self.load_case("activation-research-en.dev.json")
        data["prompt"] = "Use the research stage before choosing an implementation."
        with self.assertRaisesRegex(EvalError, "must omit stage and skill names"):
            self.validate(data)

    def test_weak_cue_case_cannot_claim_live_activation(self) -> None:
        data = self.load_case("activation-native-en.dev.json")
        data["evidence"] = "Live model activation verified."
        with self.assertRaisesRegex(EvalError, "must retain its static-only limit"):
            self.validate(data)

    def test_active_case_rejects_retired_stage_card_language(self) -> None:
        data = self.load_case("working-facts-scope-correction.dev.json")
        data["must"].append("Restore the " + "Stage Entry Card before continuing.")
        with self.assertRaisesRegex(EvalError, "retired workflow term remains"):
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
                with self.assertRaisesRegex(EvalError, error):
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
                with self.assertRaisesRegex(EvalError, error):
                    self.validate(data)

    def test_discussion_case_rejects_missing_contract_coverage(self) -> None:
        data = self.load_case("discussion-authorized-checkpoint.dev.json")
        data["expected"]["requires"].remove("observable_discussion_trigger")
        with self.assertRaisesRegex(EvalError, "discussion coverage missing"):
            self.validate(data)

    def test_discussion_usefulness_cases_isolate_each_positive_trigger(self) -> None:
        cases = {
            "discussion-explicit-save-only.dev.json": "explicit_save_or_resume_trigger",
            "discussion-handoff-only.dev.json": "handoff_or_compaction_trigger",
            "discussion-three-branch-only.dev.json": "three_real_branches_trigger",
            "discussion-short-explicit-save.dev.json": "explicit_save_or_resume_trigger",
        }
        trigger_requirements = {
            "explicit_save_or_resume_trigger",
            "handoff_or_compaction_trigger",
            "three_real_branches_trigger",
        }
        for name, trigger in cases.items():
            with self.subTest(name=name):
                data = self.load_case(name)
                requires = set(data["expected"]["requires"])
                self.assertEqual(requires & trigger_requirements, {trigger})
                self.validate(data)
                data["expected"]["requires"].remove(trigger)
                with self.assertRaisesRegex(EvalError, "discussion coverage missing"):
                    self.validate(data)

        short_control = self.load_case("discussion-short-grill.dev.json")
        self.assertFalse(
            set(short_control["expected"]["requires"]) & trigger_requirements
        )
        self.validate(short_control)

    def test_discussion_case_locks_question_and_readback_gate_coverage(self) -> None:
        for requirement in (
            "persistence_before_next_question",
            "readback_verified_anchors",
        ):
            with self.subTest(requirement=requirement):
                data = self.load_case("discussion-authorized-checkpoint.dev.json")
                data["expected"]["requires"].remove(requirement)
                with self.assertRaisesRegex(EvalError, "discussion coverage missing"):
                    self.validate(data)

    def test_discussion_case_requires_single_conclusion_continuity_coverage(self) -> None:
        data = self.load_case("discussion-single-conclusion-continuity.dev.json")
        data["expected"]["requires"].remove("same_turn_persistence_no_status_deferral")
        with self.assertRaisesRegex(EvalError, "discussion coverage missing"):
            self.validate(data)

    def test_discussion_no_input_resume_locks_read_only_coverage(self) -> None:
        data = self.load_case("discussion-resume-no-new-input.dev.json")
        data["expected"]["requires"].remove("no_schema_or_apply")
        with self.assertRaisesRegex(EvalError, "discussion coverage missing"):
            self.validate(data)

    def test_discussion_no_input_resume_rejects_mutation_commands(self) -> None:
        data = self.load_case("discussion-resume-no-new-input.dev.json")
        data["must_not"] = [
            item.replace("run schema or apply", "write only when useful")
            for item in data["must_not"]
        ]
        with self.assertRaisesRegex(EvalError, "no-input resume must forbid"):
            self.validate(data)

    def test_discussion_recovery_case_rejects_missing_human_anchor(self) -> None:
        data = self.load_case("discussion-human-recovery.dev.json")
        data["authored_artifact"] = data["authored_artifact"].replace(
            "this controls rollback safety", "this remains undecided"
        )
        with self.assertRaisesRegex(EvalError, "Still open loses its human recovery anchor"):
            self.validate(data)

    def test_plan_case_rejects_missing_brief_decision_checkpoint(self) -> None:
        data = self.load_case("plan-ask-readiness.dev.json")
        data["expected"]["requires"].remove("brief_decision_checkpoint")
        with self.assertRaisesRegex(EvalError, "ask-predicate coverage missing"):
            self.validate(data)

    def test_audience_case_rejects_missing_material_uncertainty(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] = data["authored_response"].replace(
            "how much of that improvement came from the program",
            "participants liked the program",
        )
        with self.assertRaisesRegex(EvalError, "loses material_uncertainty"):
            self.validate(data)

    def test_audience_case_rejects_workflow_first_opening(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] = (
            "I first inspected the workflow. " + data["authored_response"]
        )
        with self.assertRaisesRegex(EvalError, "includes irrelevant workflow narration"):
            self.validate(data)

    def test_audience_case_rejects_trailing_workflow_narration(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] += (
            " I then routed this through the review stage and validated the workflow."
        )
        with self.assertRaisesRegex(EvalError, "includes irrelevant workflow narration"):
            self.validate(data)

    def test_audience_case_rejects_generic_proof_status_in_positive(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] += " This cannot prove the program worked."
        with self.assertRaisesRegex(EvalError, "generic proof-status caveat"):
            self.validate(data)

    def test_audience_case_rejects_chinese_generic_proof_status(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] += " 不能据此证明项目有效。"
        with self.assertRaisesRegex(EvalError, "generic proof-status caveat"):
            self.validate(data)

    def test_audience_case_rejects_imagined_cause_list(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] += (
            " The change may instead reflect time, environment, or other support."
        )
        with self.assertRaisesRegex(EvalError, "lists imagined alternative causes"):
            self.validate(data)

    def test_audience_case_rejects_second_independent_action(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] += " Also expand the sample and collect more feedback."
        with self.assertRaisesRegex(EvalError, "second independent next action"):
            self.validate(data)

    def test_audience_case_rejects_repeated_attribution_boundary(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] += (
            " Without a comparison, we cannot tell how much came from the program."
        )
        with self.assertRaisesRegex(EvalError, "repeats the attribution boundary"):
            self.validate(data)

    def test_audience_case_requires_explicit_negative_controls(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["negative_controls"].pop()
        with self.assertRaisesRegex(EvalError, "must contain four named failure modes"):
            self.validate(data)

    def test_audience_case_rejects_irrelevant_version_and_internal_label(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        data["authored_response"] += " Version 3.0.0 calls this C8."
        with self.assertRaisesRegex(EvalError, "exposes irrelevant internal detail"):
            self.validate(data)

    def test_audience_case_requires_repeated_caveat_control_in_chinese_or_english(self) -> None:
        data = self.load_case("audience-first-community-research.dev.json")
        for control in data["negative_controls"]:
            if control["id"] == "generic_caveat_repetition":
                control["response"] = "尚未证明。"
        with self.assertRaisesRegex(
            EvalError, "must repeat a generic caveat in English or Chinese"
        ):
            self.validate(data)

    def test_audience_case_requires_internal_detail_and_caveat_clauses(self) -> None:
        for requirement in (
            "no_irrelevant_internal_detail",
            "no_generic_proof_status",
        ):
            with self.subTest(requirement=requirement):
                data = self.load_case("audience-first-community-research.dev.json")
                data["expected"]["requires"].remove(requirement)
                with self.assertRaisesRegex(EvalError, "audience coverage missing"):
                    self.validate(data)

    def test_reader_argument_case_rejects_lost_interpretation(self) -> None:
        data = self.load_case("audience-reader-argument.dev.json")
        data["authored_response"] = data["authored_response"].replace(
            "这些通道没有显示出彼此独立的空间含义",
            "这些通道压缩效率高",
        )
        with self.assertRaisesRegex(EvalError, "loses interpretation"):
            self.validate(data)

    def test_reader_argument_case_rejects_stock_proof_status(self) -> None:
        data = self.load_case("audience-reader-argument.dev.json")
        data["authored_response"] += " 尚未证明。"
        with self.assertRaisesRegex(EvalError, "stock proof-status caveat"):
            self.validate(data)

    def test_reader_argument_case_rejects_inferred_identifier_meaning(self) -> None:
        data = self.load_case("audience-reader-argument.dev.json")
        data["authored_response"] += " C8 表示八个通道。"
        with self.assertRaisesRegex(EvalError, "infers meaning from the C8 identifier"):
            self.validate(data)

    def test_reader_argument_case_requires_all_failure_controls(self) -> None:
        data = self.load_case("audience-reader-argument.dev.json")
        data["negative_controls"].pop()
        with self.assertRaisesRegex(EvalError, "reader argument negative_controls"):
            self.validate(data)

    def test_reader_argument_case_requires_term_stability_coverage(self) -> None:
        data = self.load_case("audience-reader-argument.dev.json")
        data["expected"]["requires"].remove("term_stability")
        with self.assertRaisesRegex(EvalError, "audience coverage missing"):
            self.validate(data)

    def test_continuing_mainline_case_rejects_status_displacement(self) -> None:
        data = self.load_case("audience-continuing-mainline.dev.json")
        data["turns"][1]["assistant"] = "我先更新版本并持久化讨论文档。"
        with self.assertRaisesRegex(EvalError, "turn 2 loses answer"):
            self.validate(data)

    def test_continuing_mainline_case_requires_mainline_coverage(self) -> None:
        data = self.load_case("audience-continuing-mainline.dev.json")
        data["expected"]["requires"].remove("mainline_advanced")
        with self.assertRaisesRegex(EvalError, "audience coverage missing"):
            self.validate(data)

    def test_continuing_mainline_case_rejects_control_that_follows_mainline(self) -> None:
        data = self.load_case("audience-continuing-mainline.dev.json")
        for control in data["negative_controls"]:
            if control["id"] == "topic_switch":
                control["response"] = "继续检验独立的空间区域。"
        with self.assertRaisesRegex(EvalError, "topic_switch control still follows the mainline"):
            self.validate(data)

    def test_audience_case_allows_a_brief_relevant_skill_explanation(self) -> None:
        data = self.load_case("audience-skill-explanation-contrast.dev.json")
        self.validate(data)

    def test_audience_case_rejects_engineering_inventory_after_skill_explanation(self) -> None:
        data = self.load_case("audience-skill-explanation-contrast.dev.json")
        data["authored_response"] += (
            " I opened skills/teamwork-review/SKILL.md and dispatched a subagent."
        )
        with self.assertRaisesRegex(EvalError, "engineering process inventory"):
            self.validate(data)

    def test_skill_explanation_rejects_irrelevant_route_narration(self) -> None:
        data = self.load_case("audience-skill-explanation-contrast.dev.json")
        data["authored_response"] += (
            " I routed this through the Review stage and loaded the workflow."
        )
        with self.assertRaisesRegex(EvalError, "irrelevant route or workflow narration"):
            self.validate(data)

    def test_audience_case_rejects_a_weakened_engineering_dump_control(self) -> None:
        data = self.load_case("audience-skill-explanation-contrast.dev.json")
        data["negative_control"]["response"] = (
            "The review skill is read-only, so editing needs authorization."
        )
        with self.assertRaisesRegex(EvalError, "engineering process dump loses"):
            self.validate(data)

    def test_one_sentence_fact_control_rejects_forced_cause_in_one_sentence(self) -> None:
        data = self.load_case("audience-one-sentence-fact-control.dev.json")
        data["authored_response"] = data["negative_controls"][0]["response"]
        with self.assertRaisesRegex(EvalError, "adds a forced causal explanation"):
            self.validate(data)

    def test_one_sentence_fact_control_rejects_forced_action_in_one_sentence(self) -> None:
        data = self.load_case("audience-one-sentence-fact-control.dev.json")
        data["authored_response"] = data["negative_controls"][1]["response"]
        with self.assertRaisesRegex(EvalError, "adds a forced action"):
            self.validate(data)

    def test_one_sentence_fact_control_requires_semantic_negative_controls(self) -> None:
        data = self.load_case("audience-one-sentence-fact-control.dev.json")
        data["negative_controls"][0]["response"] = (
            "`./scripts/validate.sh` is the required repository validation command."
        )
        with self.assertRaisesRegex(EvalError, "forced_cause control loses"):
            self.validate(data)

    def test_minimal_handoff_case_rejects_missing_root_translation(self) -> None:
        data = self.load_case("subagent-minimal-handoff.dev.json")
        data["expected"]["requires"].remove("root_translation")
        with self.assertRaisesRegex(EvalError, "handoff coverage missing"):
            self.validate(data)

    def test_rule_maintenance_case_rejects_missing_user_effect(self) -> None:
        data = self.load_case("rule-maintenance-audit.dev.json")
        data["expected"]["requires"].remove("user_effect")
        with self.assertRaisesRegex(EvalError, "rule-maintenance coverage missing"):
            self.validate(data)


class OutcomeFirstParityMutationTests(unittest.TestCase):
    @staticmethod
    def parity_text() -> str:
        return "\n".join(
            (
                "A plan is optional.",
                "Authority is separate from plan acceptance.",
                "Verify only the changed path or a named protected boundary.",
                "Re-enter Plan only when new evidence changes accepted scope or criteria.",
                "Fresh review only when the user asks or an accepted risk gate requires it.",
            )
        )

    def test_each_producer_rejects_an_additive_opposite_rule(self) -> None:
        sources = {
            path: self.parity_text()
            for path in (
                "skills/using-teamwork/references/workflow-contract.md",
                "skills/teamwork-execute/SKILL.md",
                "skills/using-teamwork/references/routing-policy.md",
                "skills/using-teamwork/references/role-playbook.md",
                "scripts/install/policy.sh",
                "templates/codex-agents/teamwork-worker.toml",
                "templates/cursor-agents/worker.md",
                "templates/claude-agents/worker.md",
                ".claude-plugin/plugin.json",
                ".codex-plugin/plugin.json",
            )
        }
        opposites = (
            ("A plan is mandatory.", "mandatory plan"),
            ("Every change requires the full test suite.", "every full suite"),
            ("Always perform a fresh review after implementation.", "automatic fresh/final review"),
            ("Confirmation grants implementation authority.", "confirmation grants authority"),
        )
        for path in sources:
            for opposite, error in opposites:
                with self.subTest(path=path, opposite=opposite):
                    mutated = dict(sources)
                    mutated[path] += "\n" + opposite
                    with self.assertRaisesRegex(EvalError, error):
                        validate_outcome_first_source_parity(mutated)


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
        cls.policy = (ROOT / "scripts/install/policy.sh").read_text(encoding="utf-8")
        cls.plan_output = (
            ROOT / "skills/using-teamwork/references/plan-output.md"
        ).read_text(encoding="utf-8")
        cls.subagent_contract = (
            ROOT / "skills/using-teamwork/references/subagent-contract.md"
        ).read_text(encoding="utf-8")
        cls.subagent_dispatch = (
            ROOT / "skills/using-teamwork/references/subagent-dispatch.md"
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
            for skill, (path, _) in SKILL_SOURCE_CONTRACTS.items()
        }

    def assert_skill_contract_rejected(
        self, skill: str, old: str, new: str, error: str
    ) -> None:
        source = self.skill_sources[skill]
        mutated = source.replace(old, new)
        self.assertNotEqual(mutated, source, f"mutation did not change {skill}")
        with self.assertRaisesRegex(EvalError, error):
            validate_skill_source_contract(skill, mutated)

    def test_natural_intent_descriptions_are_source_contracts(self) -> None:
        mutations = {
            "teamwork-research": ("the user needs facts checked before action", "the stage is available", "natural research intent"),
            "teamwork-debug": ("a failure, crash, flake, regression, or unexpected result has an unknown cause", "the stage is available", "unknown-cause debug intent"),
            "teamwork-execute": ("the user asks to implement, build, change, fix, or continue scoped work", "the stage is available", "natural execute intent"),
            "teamwork-review": ("the user asks whether work is correct or complete", "the stage is available", "natural review intent"),
            "teamwork-goal": ("the user asks Codex to keep working until a verifiable result", "the stage is available", "natural goal intent"),
            "teamwork-init": ("a project needs agent instructions or Teamwork context set up", "the stage is available", "natural init intent"),
            "teamwork-update": ("the user asks to check or refresh globally installed Teamwork skills", "the stage is available", "natural update intent"),
        }
        for skill, (old, new, error) in mutations.items():
            with self.subTest(skill=skill):
                self.assert_skill_contract_rejected(skill, old, new, error)

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
        with self.assertRaisesRegex(EvalError, error):
            validate_mainline_focus_source_text(
                sources["grill"],
                sources["project_init"],
                sources["teamwork_init"],
            )

    def assert_discussion_protocol_rejected(
        self, old: str, new: str, error: str
    ) -> None:
        protocol = (
            ROOT / "skills/using-teamwork/references/artifact-protocol.md"
        ).read_text(encoding="utf-8")
        mutated = protocol.replace(old, new)
        self.assertNotEqual(mutated, protocol, "discussion mutation did not apply")
        with self.assertRaisesRegex(EvalError, error):
            validate_discussion_source_text(
                self.skill_sources["grill-me"],
                self.skill_sources["using-teamwork"],
                mutated,
                self.discussion_template,
            )

    def test_rejects_retired_review_severity_taxonomy(self) -> None:
        mutated = self.review.replace(
            "one class: `BLOCKER`, `FOLLOW-UP`, or `SUGGESTION`",
            "one class: `blocker`, `major`, or `minor`",
        )
        with self.assertRaisesRegex(EvalError, "review taxonomy must be"):
            validate_semantic_source_text(mutated, self.goal, self.role_playbook)

    def test_rejects_retired_role_playbook_severity_taxonomy(self) -> None:
        mutated = self.role_playbook.replace(
            "`BLOCKER | FOLLOW-UP | SUGGESTION` findings",
            "`blocker | major | minor` findings",
        )
        with self.assertRaisesRegex(EvalError, "role-playbook.md: review taxonomy must be"):
            validate_semantic_source_text(self.review, self.goal, mutated)

    def test_rejects_goal_activation_merely_when_available(self) -> None:
        mutated = self.goal.replace(
            "only when the user explicitly requests Goal mode or\naccepts a Goal Proposal",
            "when available",
        )
        with self.assertRaisesRegex(EvalError, "explicit user request or accepted Goal Proposal"):
            validate_semantic_source_text(self.review, mutated, self.role_playbook)

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
            "authorized change/build work stays native or goes straight to Execute",
            "All tasks enter a Teamwork stage",
            "Native fast path",
        )

    def test_using_teamwork_rejects_research_for_a_known_facts_explanation(self) -> None:
        self.assert_skill_contract_rejected(
            "using-teamwork",
            "When all decision-relevant facts are\n"
            "supplied, a stable explanation stays native",
            "Every explanation enters Research",
            "known-facts native explanation",
        )

    def test_using_teamwork_rejects_repeated_supplied_facts_explanation(self) -> None:
        self.assert_skill_contract_rejected(
            "using-teamwork",
            "For a supplied-facts explanation, name\n"
            "the conclusion and missing discriminator once, then stop",
            "For supplied facts, list imagined causes and repeat the conclusion",
            "supplied-facts concise explanation",
        )

    def test_grill_rejects_removed_explicit_activation(self) -> None:
        self.assert_skill_contract_rejected(
            "grill-me",
            "Enter only for a user-originated challenge or question-first request",
            "Enter whenever available",
            "explicit activation",
        )

    def test_grill_frontmatter_rejects_plan_activation_overlap(self) -> None:
        mutated = self.skill_sources["grill-me"].replace(
            "or continues that discussion;",
            "or a non-simple Plan auto-enters;",
        )
        self.assertNotEqual(mutated, self.skill_sources["grill-me"])
        with self.assertRaisesRegex(EvalError, "must not overlap Plan activation"):
            validate_skill_source_contract("grill-me", mutated)

    def test_grill_rejects_plan_complexity_activation(self) -> None:
        self.assert_skill_contract_rejected(
            "grill-me",
            "Plan complexity, artifact usefulness, and ordinary\nclarification do not activate Grill",
            "Plan complexity activates Grill",
            "Plan complexity stays out",
        )

    def test_grill_requires_an_evidence_backed_recommendation_per_question(self) -> None:
        self.assert_skill_contract_rejected(
            "grill-me",
            "Before each\nquestion, inspect discoverable evidence and give grounded recommendation",
            "Ask the user to choose without a recommendation",
            "evidence-backed recommended answer",
        )

    def test_grill_requires_a_concise_text_fallback(self) -> None:
        self.assert_skill_contract_rejected(
            "grill-me",
            "host's native interaction surface if callable, else one\nconcise text question",
            "and stop when it is unavailable",
            "concise text fallback",
        )

    def test_grill_rejects_mutating_a_no_input_resume(self) -> None:
        grill = self.skill_sources["grill-me"].replace(
            "update only for new input\nand close when scope resolves.",
            "On every continuation, update or close before replying.",
        )
        self.assertNotEqual(grill, self.skill_sources["grill-me"])
        with self.assertRaisesRegex(EvalError, "continued Grill mutation boundary"):
            validate_discussion_source_text(
                grill,
                self.skill_sources["using-teamwork"],
                (
                    ROOT
                    / "skills/using-teamwork/references/artifact-protocol.md"
                ).read_text(encoding="utf-8"),
                self.discussion_template,
            )

    def test_research_rejects_collapsed_evidence_tiers(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-research",
            "`observed`, `inferred`,\nand `claimed` findings",
            "`claimed` findings",
            "observed/inferred/claimed evidence",
        )

    def test_research_rejects_explaining_supplied_facts_as_research(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-research",
            "Do not enter merely to explain supplied facts when no lookup\n"
            "or stale-assumption check is needed; return to Native",
            "Enter Research for every supplied-facts explanation",
            "supplied-facts native boundary",
        )

    def test_debug_rejects_unbounded_evidence_gathering(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-debug",
            "Gather only evidence that distinguishes the next possible fix",
            "collect any evidence",
            "discriminating evidence only",
        )

    def test_plan_rejects_complexity_activating_grill(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-plan",
            "Plan complexity never activates `grill-me`",
            "Plan complexity activates `grill-me`",
            "Plan complexity does not activate Grill",
        )

    def test_execute_rejects_proxy_success(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-execute",
            "Never substitute plan/mock/static success for an available real path",
            "Treat plan/mock/static success as completion",
            "proxy checks cannot replace delivery",
        )

    def test_init_rejects_global_failure_hard_gate(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-init",
            "Project instructions, memory,\nand CodeGraph context can continue when the global install returns an actionable\nconfiguration failure",
            "Project instructions, memory, and CodeGraph context stop when the global install returns an actionable configuration failure",
            "safe project-context continuation",
        )

    def test_update_rejects_release_metadata_scope(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-update",
            "Never edit `VERSION`, plugin manifests, changelogs, release commits, tags, or\n  GitHub Releases",
            "Edit VERSION and publish a GitHub Release",
            "no release metadata",
        )

    def test_update_rejects_taking_over_project_initialization(self) -> None:
        self.assert_skill_contract_rejected(
            "teamwork-update",
            "Project initialization and project-context\nchanges belong to `teamwork-init`",
            "Update initializes and rewrites project context itself",
            "project initialization ownership",
        )

    def test_update_rejects_additive_publication_authority(self) -> None:
        mutated = self.skill_sources["teamwork-update"] + (
            "\nWith explicit publication authority, edit VERSION and plugin manifests, "
            "write the changelogs and release commit, create the tag, and publish the "
            "GitHub Release.\n"
        )
        with self.assertRaisesRegex(EvalError, "must not authorize maintainer publication"):
            validate_release_boundary_source_text(
                mutated,
                self.skill_sources["using-teamwork"],
                self.check_update,
                self.codex,
                False,
            )

    def test_release_policy_rejects_duplication_outside_agents(self) -> None:
        mutated_codex = self.codex + "\nOne release unit contains VERSION and tags.\n"
        with self.assertRaisesRegex(EvalError, "must live only in root AGENTS.md"):
            validate_release_boundary_source_text(
                self.skill_sources["teamwork-update"],
                self.skill_sources["using-teamwork"],
                self.check_update,
                mutated_codex,
                False,
            )

    def test_release_policy_rejects_restored_changelog_guide(self) -> None:
        with self.assertRaisesRegex(EvalError, "changelog-guide.md"):
            validate_release_boundary_source_text(
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
        with self.assertRaisesRegex(EvalError, "user-facing changelog"):
            validate_maintainer_release_source_text(mutated)

    def test_maintainer_release_rejects_partial_release_unit(self) -> None:
        mutated = self.agents.replace(
            "One release unit\ncontains `VERSION`, both plugin manifests, both changelogs",
            "One release unit contains VERSION only",
        )
        self.assertNotEqual(mutated, self.agents)
        with self.assertRaisesRegex(EvalError, "complete release unit"):
            validate_maintainer_release_source_text(mutated)

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
                with self.assertRaisesRegex(EvalError, error):
                    validate_minimality_source_text(
                        workflow_contract, self.review_lenses
                    )

    def test_always_loaded_policy_rejects_deleted_audience_boundary(self) -> None:
        mutated = self.policy.replace(
            "Lead with conclusion.",
            "Put the conclusion last.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "audience-first reply"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_requires_a_connected_reader_argument(self) -> None:
        mutated = self.policy.replace(
            "Connect observed\n"
            "basis, plain interpretation, and decision-relevant boundary/next check.",
            "List observations without connecting them to a decision.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "connected reader argument"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_requires_observation_inference_separation(self) -> None:
        mutated = self.policy.replace(
            "Separate\nobservation from inference.",
            "Blend observation and inference together.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "observation/inference separation"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_preserves_concise_default_prose(self) -> None:
        mutated = self.policy.replace(
            "Avoid headings; simple facts stay one sentence.",
            "Use headings and expand simple facts.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "concise default prose"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_rejects_inferred_label_meaning(self) -> None:
        mutated = self.policy.replace(
            "Use supplied\nterms; invent no labels or identifier meanings.",
            "Infer a label's meaning whenever it sounds suggestive.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "stable terms"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_requires_the_specific_ask_gate(self) -> None:
        mutated = self.policy.replace(
            "Ask only for required input/observation or material user decisions",
            "Ask only when required",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "specific Ask Gate"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_requires_grounded_claims(self) -> None:
        mutated = self.policy.replace("Ground claims", "Guess claims")
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "grounded claims"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_requires_scope_control(self) -> None:
        mutated = self.policy.replace("keep scope", "broaden scope")
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "scope boundary"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_routes_material_decisions_to_plan(self) -> None:
        mutated = self.policy.replace(
            "unresolved scope/contract/architecture choices to plan",
            "material decisions directly to execution",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "material decision routing"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_preserves_grill_authority_provenance(self) -> None:
        mutated = self.policy.replace(
            "Grill only for user-originated challenge/question-first intent;\n"
            "reuse/artifact usefulness grants no write.",
            "Any automatic Plan or useful artifact condition grants discussion writes.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "explicit Grill boundary"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_requires_direct_change_build(self) -> None:
        mutated = self.policy.replace(
            "Clear authorized change/build\ngoes straight to implementation.",
            "Clear change/build goes through planning and review.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "direct change/build"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_preserves_full_relevance_gate(self) -> None:
        mutated = self.policy.replace(
            "detail affecting understanding/decision/action/risk/confidence",
            "decision detail",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "relevance gate"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_keeps_request_user_input_codex_only(self) -> None:
        mutated = self.policy.replace(
            "In Codex, call request_user_input for a question when it is callable.",
            "Use the ordinary shared policy for Codex questions.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "Codex policy must call request_user_input"):
            validate_always_loaded_policy_text(mutated)

    def test_always_loaded_policy_requires_missing_discriminator_uncertainty(self) -> None:
        mutated = self.policy.replace(
            "State uncertainty once.",
            "Repeat a generic caveat without a decision boundary.",
        )
        self.assertNotEqual(mutated, self.policy)
        with self.assertRaisesRegex(EvalError, "decision-boundary uncertainty"):
            validate_always_loaded_policy_text(mutated)

    def test_audience_source_rejects_deleted_relevance_gate(self) -> None:
        mutated = self.workflow_contract.replace(
            "Use a relevance gate.", "Always include every implementation detail."
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "relevance gate"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_conclusion_last(self) -> None:
        mutated = self.workflow_contract.replace(
            "Lead with the conclusion the user needs.",
            "Build up to the conclusion at the end.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "conclusion-first user need"):
            validate_audience_source_text(mutated)

    def test_audience_source_requires_a_connected_reader_argument(self) -> None:
        mutated = self.workflow_contract.replace(
            "For a substantive explanation or\n"
            "discussion, make one connected argument: conclusion, observed basis,\n"
            "plain-language interpretation, and, only if it changes a decision, a concrete\n"
            "boundary or next discriminator.",
            "For a substantive explanation, list observations without an argument.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "connected reader argument"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_generic_proof_status(self) -> None:
        mutated = self.workflow_contract.replace(
            "Do not substitute a stock proof-status sentence for that boundary.",
            "use a generic proof-status disclaimer",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "no stock proof-status"):
            validate_audience_source_text(mutated)

    def test_audience_source_requires_a_concrete_evidence_boundary(self) -> None:
        mutated = self.workflow_contract.replace(
            "Treat uncertainty as a decision boundary: say what the evidence supports, what\n"
            "it cannot decide, and what comparison, measurement, or observation would change\n"
            "the decision.",
            "Prefer a stock uncertainty disclaimer.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "decision-boundary uncertainty"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_repeated_concluding_limitation(self) -> None:
        mutated = self.workflow_contract.replace(
            "Once the conclusion and decision boundary are\n"
            "clear, stop; do not restate them.",
            "Repeat the limitation again in the conclusion.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "stop after the decision boundary"):
            validate_audience_source_text(mutated)

    def test_audience_source_explains_the_missing_discriminator(self) -> None:
        mutated = self.workflow_contract.replace(
            "Treat uncertainty as a decision boundary: say what the evidence supports, what\n"
            "it cannot decide, and what comparison, measurement, or observation would change\n"
            "the decision.",
            "List every imagined cause of uncertainty.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "decision-boundary uncertainty"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_irrelevant_alternative_causes(self) -> None:
        mutated = self.workflow_contract.replace(
            "Mention an alternative cause only when it changes action or confidence.",
            "Name every possible alternative cause.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "alternative-cause relevance"):
            validate_audience_source_text(mutated)

    def test_audience_source_allows_relevant_skill_explanations(self) -> None:
        mutated = self.workflow_contract.replace(
            "A brief skill name or\n"
            "explanation is allowed when it clarifies a capability, limitation, or reason for\n"
            "the approach.",
            "Never name a skill in a user-facing reply.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "useful skill explanation"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_engineering_process_inventory(self) -> None:
        mutated = self.workflow_contract.replace(
            "Omit engineering process and implementation inventory—such as\n"
            "routes, files, subagents, and test counts—unless relevant.",
            "List routes, files, subagents, and test counts in every reply.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "irrelevant engineering inventory"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_forced_multi_part_answers(self) -> None:
        mutated = self.workflow_contract.replace(
            "This is an order of reasoning, not headings or a fixed answer template.",
            "Always answer in four sections: fact, cause, conclusion, and next action.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "no fixed answer template"):
            validate_audience_source_text(mutated)

    def test_audience_source_requires_observation_inference_separation(self) -> None:
        mutated = self.workflow_contract.replace(
            "State observed facts separately from inference.",
            "Blend observations and inference together.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "observation/inference separation"):
            validate_audience_source_text(mutated)

    def test_audience_source_requires_discussion_mainline(self) -> None:
        mutated = self.workflow_contract.replace(
            "In a continuing discussion, retain the current question or decision.",
            "Start each continuing reply with a different topic.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "discussion mainline"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_coined_labels(self) -> None:
        mutated = self.workflow_contract.replace(
            "Use the user's or\n"
            "repository's established terms; define a necessary unfamiliar term before using\n"
            "it, and never coin a label to organize an answer.",
            "Invent a new label whenever it makes the response sound organized.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "stable terms"):
            validate_audience_source_text(mutated)

    def test_audience_source_rejects_inferred_identifier_meaning(self) -> None:
        mutated = self.workflow_contract.replace(
            "Treat a supplied identifier as\n"
            "a name, not evidence of its contents; never infer a number, property, or causal\n"
            "role from it.",
            "Infer a number or property directly from an identifier.",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "identifier semantics"):
            validate_audience_source_text(mutated)

    def test_rule_maintenance_source_rejects_missing_user_effect_audit(self) -> None:
        mutated = self.workflow_contract.replace(
            "Confirm the canonical owner and\n"
            "   user-visible effect; check only the changed rule or a named protected boundary.",
            "minimize the internal wording",
        )
        self.assertNotEqual(mutated, self.workflow_contract)
        with self.assertRaisesRegex(EvalError, "canonical owner and user effect"):
            validate_rule_maintenance_source_text(mutated)

    def test_decision_checkpoint_rejects_lost_still_open_field(self) -> None:
        plan = self.skill_sources["teamwork-plan"].replace(
            "`Still open: ...`", "`Resolved: ...`"
        )
        self.assertNotEqual(plan, self.skill_sources["teamwork-plan"])
        with self.assertRaisesRegex(EvalError, "Still open field"):
            validate_decision_checkpoint_source_text(
                self.workflow_contract, plan, self.plan_output
            )

    def test_minimal_handoff_rejects_deleted_direct_evidence(self) -> None:
        mutated = self.subagent_contract.replace(
            "Direct Evidence:", "Notes:"
        )
        self.assertNotEqual(mutated, self.subagent_contract)
        with self.assertRaisesRegex(EvalError, "Direct Evidence"):
            validate_minimal_handoff_source_text(mutated, self.subagent_dispatch)

    def test_grill_rejects_lost_mainline(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "Keep goal/current focus: one decision at a time; each question advances\n"
            "decision.",
            "Follow the latest local topic.",
            "keep goal/current focus",
        )

    def test_grill_rejects_irrelevant_questions(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "drop distractions; never repeat answered decisions.",
            "Ask any locally interesting question.",
            "drop distractions",
        )

    def test_grill_rejects_adjacent_question_after_stated_scope_is_resolved(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "Do not promote a consequence of a settled answer into a new user decision unless\n"
            "the original request named that decision; stop at the requested boundary.",
            "Promote a consequence of a settled answer into a new user decision.",
            "requested boundary",
        )

    def test_grill_rejects_per_turn_mainline_ribbon(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "restate without\nrepetition;",
            "repeat that link on every turn.",
            "restate without repetition",
        )

    def test_grill_rejects_internal_route_status_in_an_ordinary_reply(self) -> None:
        self.assert_mainline_focus_rejected(
            "grill",
            "Use user's domain language",
            "Ask with internal route labels",
            "use user's domain language",
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
        with self.assertRaisesRegex(EvalError, "singular discussion path"):
            validate_discussion_source_text(
                self.skill_sources["grill-me"],
                self.skill_sources["using-teamwork"],
                mutated,
                self.discussion_template,
            )

    def test_discussion_source_rejects_broadened_explicit_grill_authority(self) -> None:
        grill = self.skill_sources["grill-me"]
        mutated = grill.replace(
            "Explicit Grill\nauthorizes only its supporting `docs/teamwork/` discussion record unless the user\n"
            "says no files.",
            "Explicit Grill authorizes all project writes.",
        )
        self.assertNotEqual(mutated, grill)
        with self.assertRaisesRegex(EvalError, "narrow explicit-Grill write authority"):
            validate_discussion_source_text(
                mutated,
                self.skill_sources["using-teamwork"],
                (ROOT / "skills/using-teamwork/references/artifact-protocol.md").read_text(
                    encoding="utf-8"
                ),
                self.discussion_template,
            )

    def test_discussion_source_rejects_plan_complexity_activation(self) -> None:
        grill = self.skill_sources["grill-me"]
        mutated = grill.replace(
            "Plan complexity, artifact usefulness, and ordinary\n"
            "clarification do not activate Grill or create authority.",
            "Plan complexity activates Grill and grants discussion writes.",
        )
        self.assertNotEqual(mutated, grill)
        with self.assertRaisesRegex(EvalError, "Plan complexity stays out"):
            validate_discussion_source_text(
                mutated,
                self.skill_sources["using-teamwork"],
                (ROOT / "skills/using-teamwork/references/artifact-protocol.md").read_text(
                    encoding="utf-8"
                ),
                self.discussion_template,
            )

    def test_discussion_source_rejects_usefulness_as_authority(self) -> None:
        protocol = (ROOT / "skills/using-teamwork/references/artifact-protocol.md").read_text(
            encoding="utf-8"
        )
        mutated = protocol.replace(
            "These conditions decide usefulness, never authority.",
            "These useful conditions grant write authority.",
        )
        self.assertNotEqual(mutated, protocol)
        with self.assertRaisesRegex(EvalError, "usefulness-authority separation"):
            validate_discussion_source_text(
                self.skill_sources["grill-me"],
                self.skill_sources["using-teamwork"],
                mutated,
                self.discussion_template,
            )

    def test_discussion_source_rejects_additive_absolute_short_grill_rule(self) -> None:
        grill = self.skill_sources["grill-me"]
        mutated = grill + "\nShort Grill stays artifact-free.\n"
        with self.assertRaisesRegex(EvalError, "absolute short-Grill rule"):
            validate_discussion_source_text(
                mutated,
                self.skill_sources["using-teamwork"],
                (ROOT / "skills/using-teamwork/references/artifact-protocol.md").read_text(
                    encoding="utf-8"
                ),
                self.discussion_template,
            )

    def test_discussion_source_requires_entry_time_protocol_load(self) -> None:
        grill = self.skill_sources["grill-me"]
        mutated = grill.replace(
            "`skills/using-teamwork/references/artifact-protocol.md` completely at entry.",
            "`skills/using-teamwork/references/artifact-protocol.md` before discussion access.",
        )
        self.assertNotEqual(mutated, grill)
        with self.assertRaisesRegex(EvalError, "entry-time protocol load"):
            validate_discussion_source_text(
                mutated,
                self.skill_sources["using-teamwork"],
                (ROOT / "skills/using-teamwork/references/artifact-protocol.md").read_text(
                    encoding="utf-8"
                ),
                self.discussion_template,
            )

    def test_discussion_source_rejects_persistence_status_deferral(self) -> None:
        grill = self.skill_sources["grill-me"]
        mutated = grill.replace(
            "Never emit plan/status; first visible text follows success.",
            "Tell the user that the record will be saved later.",
        )
        self.assertNotEqual(mutated, grill)
        with self.assertRaisesRegex(EvalError, "same-turn persistence"):
            validate_discussion_source_text(
                mutated,
                self.skill_sources["using-teamwork"],
                (ROOT / "skills/using-teamwork/references/artifact-protocol.md").read_text(
                    encoding="utf-8"
                ),
                self.discussion_template,
            )

    def test_discussion_source_preserves_observable_triggers(self) -> None:
        mutations = (
            ("the user explicitly asks to save or resume later", "the discussion feels long"),
            ("a known handoff or context compaction is approaching", "ten minutes pass"),
            (
                "a material conclusion is settled and a distinct comparison, measurement, or\n"
                "  decision remains open before the next action",
                "enough words have accumulated",
            ),
            (
                "Do not wait for a second settled choice when the first conclusion already\n"
                "determines an open next check.",
                "Wait for two settled choices before saving.",
            ),
            ("one decision has at least three real branches", "the agent feels uncertain"),
            (
                "Time, word count, and a short Grill never trigger persistence",
                "Time and word count trigger persistence",
            ),
        )
        for old, new in mutations:
            with self.subTest(old=old):
                self.assert_discussion_protocol_rejected(old, new, "discussion contract")

    def test_discussion_source_preserves_runnable_helper_interface(self) -> None:
        self.assert_discussion_protocol_rejected(
            "From the project root, run `inspect`; the helper defaults its project root to\n"
            "   the current directory.",
            "Run inspect with unspecified required arguments.",
            "cwd-default inspect",
        )
        self.assert_discussion_protocol_rejected(
            "in exactly one\n   `apply --request-json <JSON>`",
            "in an unspecified apply operation",
            "single structured apply",
        )
        self.assert_discussion_protocol_rejected(
            "Never use stdin.",
            "Pass the request through stdin.",
            "no stdin apply",
        )

    def test_discussion_source_preserves_supporting_privacy_boundary(self) -> None:
        self.assert_discussion_protocol_rejected(
            "Keep privacy-safe summaries, never hidden reasoning, secrets, unnecessary\n"
            "personal data, or a transcript.",
            "Store the complete transcript, secrets, and hidden reasoning.",
            "privacy boundary",
        )

    def test_discussion_source_requires_five_recovery_sections(self) -> None:
        self.assert_discussion_protocol_rejected(
            "Goal, Settled (including reasons), Still open, Key evidence,\n"
            "and Continue here",
            "Goal and Notes",
            "five human recovery sections",
        )

    def test_discussion_source_requires_new_input_for_updates_and_scope_close(self) -> None:
        self.assert_discussion_protocol_rejected(
            "Update only when the user's new input changes saved decisions, evidence, or the\n"
            "continuation point, not merely because a turn resumed",
            "Update on every turn",
            "new-input-only updates",
        )
        self.assert_discussion_protocol_rejected(
            "Opening, recovering, or\n"
            "reading an existing discussion is read-only: after `inspect`, do not run `schema`\n"
            "or `apply`; ask the saved unresolved question",
            "Opening a discussion permits schema update and apply before asking a refined question",
            "read-only resume",
        )
        self.assert_discussion_protocol_rejected(
            "The user's stated\nGrill scope defines closure",
            "Continue into adjacent decisions after the stated scope is complete",
            "scope-bounded closure",
        )

    def test_discussion_source_requires_helper_as_sole_runtime_path(self) -> None:
        self.assert_discussion_protocol_rejected(
            "This helper is the sole runtime path for discussion\nstate",
            "Edit the canonical discussion files directly",
            "helper sole runtime path",
        )

    def test_discussion_source_requires_inspect_first_and_only_read_path(self) -> None:
        self.assert_discussion_protocol_rejected(
            "From the project root, run `inspect`; the helper defaults its project root to\n"
            "   the current directory",
            "Read index.json directly before running inspect",
            "cwd-default inspect",
        )
        self.assert_discussion_protocol_rejected(
            "Its result is the only discovery and reading source for\n"
            "   canonical discussion state, anchors, and artifacts",
            "Use searches and direct file reads to discover discussion state",
            "inspect sole read path",
        )

    def test_discussion_source_rejects_direct_canonical_file_access(self) -> None:
        self.assert_discussion_protocol_rejected(
            "do not directly read\n"
            "   `index.json`, `current.md`, `README.md`, or a discussion artifact",
            "open index.json, current.md, README.md, and the artifact directly",
            "no direct canonical reads",
        )
        self.assert_discussion_protocol_rejected(
            "do not edit canonical files or substitute shell, validators, or another transaction",
            "Edit index.json and current.md directly with a shell validator",
            "no direct or ad-hoc write path",
        )

    def test_discussion_source_requires_semantic_record_and_opaque_revision(self) -> None:
        self.assert_discussion_protocol_rejected(
            "The helper derives the path,\n   index entry, and rendered artifact",
            "Manually choose a path and render the index entry and artifact",
            "semantic helper rendering",
        )
        self.assert_discussion_protocol_rejected(
            "Run\n   `schema <operation>` and fill exactly its JSON shape",
            "Construct an undocumented request by reading the helper source.",
            "self-describing request schema",
        )
        self.assert_discussion_protocol_rejected(
            "`decision_map.action` is `preserve`, `clear`, `replace`, or create-only\n"
            "   `omit`",
            "Decision-map actions are undocumented.",
            "decision-map action grammar",
        )
        self.assert_discussion_protocol_rejected(
            "Reuse the opaque `revision` unchanged",
            "Recompute or alter revision before apply",
            "opaque revision reuse",
        )

    def test_discussion_source_requires_one_structured_apply(self) -> None:
        self.assert_discussion_protocol_rejected(
            "in exactly one\n   `apply --request-json <JSON>`",
            "using multiple direct write operations",
            "single structured apply",
        )
        self.assert_discussion_protocol_rejected(
            "`apply` is the only writer",
            "direct file edits are also supported writers",
            "apply sole writer",
        )

    def test_discussion_source_rejects_close_then_create_replacement(self) -> None:
        self.assert_discussion_protocol_rejected(
            "never close and\n"
            "then create as separate transactions",
            "close the old record, then create the replacement separately",
            "no close-create replacement",
        )

    def test_discussion_source_requires_atomic_replacement(self) -> None:
        self.assert_discussion_protocol_rejected(
            "Replacement atomically supersedes the\n"
            "old record, links it to the new record, and activates the new one",
            "Replacement may leave the old record active while creating the new one",
            "atomic replacement",
        )

    def test_discussion_source_forbids_manual_fallback_after_helper_failure(self) -> None:
        self.assert_discussion_protocol_rejected(
            "Never manually repair or complete canonical state after a nonzero helper exit",
            "After helper failure, patch the canonical files manually",
            "no manual fallback write",
        )
        self.assert_discussion_protocol_rejected(
            "Do not use this fallback\nafter an attempted `apply`",
            "Use the natural-language fallback after a partial apply",
            "no post-apply fallback",
        )

    def test_discussion_source_requires_bounded_prewrite_fallback(self) -> None:
        self.assert_discussion_protocol_rejected(
            "Before writing, absent discussion authority, `initialized: false`, a user\n"
            "no-files request, or host read-only state uses a natural-language fallback",
            "Any helper failure uses a fallback",
            "pre-write fallback conditions",
        )
        self.assert_discussion_protocol_rejected(
            "goal,\nsettled choices, open choice, key evidence, and continuation point",
            "a generic unavailable message",
            "plain fallback recovery",
        )
        self.assert_discussion_protocol_rejected(
            "State once\nthat it was not saved and may be lost across sessions",
            "Silently omit persistence",
            "one-time continuity warning",
        )

    def test_discussion_source_requires_helper_failures_to_stop(self) -> None:
        self.assert_discussion_protocol_rejected(
            "stop the dependent question and any completion claim",
            "continue questioning and claim completion",
            "helper failure stop",
        )

    def test_discussion_source_allows_relevant_skill_explanation(self) -> None:
        protocol = (
            ROOT / "skills/using-teamwork/references/artifact-protocol.md"
        ).read_text(encoding="utf-8")
        mutated = protocol.replace(
            "A brief skill name or purpose is welcome when it helps explain a\n"
            "capability, limit, or choice",
            "Never mention a skill or its purpose",
        )
        self.assertNotEqual(mutated, protocol)
        with self.assertRaisesRegex(EvalError, "useful skill explanation"):
            validate_discussion_source_text(
                self.skill_sources["grill-me"],
                self.skill_sources["using-teamwork"],
                mutated,
                self.discussion_template,
            )

    def test_discussion_source_keeps_continuity_only_user_reply(self) -> None:
        self.assert_discussion_protocol_rejected(
            "saved decisions, current resume context, or completed\n"
            "discussion",
            "paths, gates, checks, and helper process",
            "continuity-value reply",
        )

    def test_discussion_template_rejects_missing_required_sections(self) -> None:
        for heading, error in (
            ("## Goal", "Goal"),
            ("## Settled", "Settled"),
            ("## Still open", "Still open"),
            ("## Key evidence", "Key evidence"),
            ("## Continue here", "Continue here"),
        ):
            with self.subTest(heading=heading):
                mutated = self.discussion_template.replace(heading, f"## Removed {heading}")
                with self.assertRaisesRegex(EvalError, error):
                    validate_discussion_template_text(mutated)

    def test_discussion_template_requires_supporting_authority(self) -> None:
        mutated = self.discussion_template.replace(
            "Authority: supporting", "Authority: canonical"
        )
        with self.assertRaisesRegex(EvalError, "Authority: supporting"):
            validate_discussion_template_text(mutated)

    def test_discussion_template_requires_a_specific_topic_h1(self) -> None:
        mutated = self.discussion_template.replace(
            "# <Specific decision or continuation title>", "# Discussion"
        )
        self.assertNotEqual(mutated, self.discussion_template)
        with self.assertRaisesRegex(EvalError, "specific topic H1"):
            validate_discussion_template_text(mutated)

    def test_discussion_template_requires_recovery_reasoning(self) -> None:
        mutated = self.discussion_template.replace(
            "why it guides the next decision", "that it was chosen"
        )
        self.assertNotEqual(mutated, self.discussion_template)
        with self.assertRaisesRegex(EvalError, "Settled must preserve why it guides the next decision"):
            validate_discussion_template_text(mutated)

    def test_discussion_template_requires_observed_basis(self) -> None:
        mutated = self.discussion_template.replace(
            "observed basis", "general confidence"
        )
        self.assertNotEqual(mutated, self.discussion_template)
        with self.assertRaisesRegex(EvalError, "Settled must preserve observed basis"):
            validate_discussion_template_text(mutated)

    def test_discussion_handoff_rejects_repeated_answered_decision(self) -> None:
        path = ROOT / "evals/teamwork/cases/discussion-handoff-recovery.dev.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["trajectory"][0]["assistant"] = (
            "We already decided to use a dedicated discussion artifact and "
            "persist only when an observable trigger is present.\n"
            "Should we use a dedicated discussion artifact?"
        )
        with self.assertRaisesRegex(EvalError, "repeats answered decision"):
            validate_discussion_handoff_case(data, path)



if __name__ == "__main__":
    unittest.main()
