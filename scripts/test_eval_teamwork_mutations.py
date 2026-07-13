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
            EVAL.validate_case(path, {"assistance-quality"})

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


if __name__ == "__main__":
    unittest.main()
