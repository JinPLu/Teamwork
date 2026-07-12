#!/usr/bin/env python3
"""Mutation tests for grill trajectory false-positive resistance."""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Callable

from grill_contract import active_output_violation, close_basis, exit_authority_is_grounded


ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "scripts" / "eval-teamwork.py"
SOURCE = ROOT / "evals" / "teamwork" / "outputs" / "question-first" / "dev.jsonl"


class GrillMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]

    def assert_rejected(self, case_id: str, mutate: Callable[[dict], None]) -> None:
        rows = copy.deepcopy(self.rows)
        row = next(item for item in rows if item["case_id"] == case_id)
        mutate(row)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "question-first"
            output.mkdir()
            (output / "dev.jsonl").write_text(
                "\n".join(json.dumps(item, separators=(",", ":")) for item in rows) + "\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["TEAMWORK_EVAL_OUTPUT_DIR"] = temp
            completed = subprocess.run(
                [sys.executable, str(EVAL), "--split", "dev"],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0, completed.stdout)

    def test_missing_active_marker(self) -> None:
        self.assert_rejected("question-first-explicit-grill", lambda row: row["trajectory"][0].update(assistant="Question: Keep compatibility?\nRecommended: Yes.\nAlternatives: No."))

    def test_two_questions(self) -> None:
        self.assert_rejected("question-first-explicit-grill", lambda row: row["trajectory"][0].update(assistant=row["trajectory"][0]["assistant"] + "\nQuestion: Also migrate now?"))

    def test_missing_recommendation(self) -> None:
        self.assert_rejected("question-first-explicit-grill", lambda row: row["trajectory"][0].update(assistant=row["trajectory"][0]["assistant"].replace("Recommended:", "Suggestion:")))

    def test_premature_plan_or_edit(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][0]["assistant"] += "\nI edited the file and wrote the implementation."
        self.assert_rejected("question-first-explicit-grill", mutate)

    def test_answer_treated_as_exit(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][1]["assistant"] = "Grill status: closed\nExit authority: User chose compatibility."
        self.assert_rejected("grill-multiturn-continuation-exit", mutate)

    def test_close_without_grounded_authority(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][-1]["assistant"] = row["trajectory"][-1]["assistant"].replace(
                "Exit authority: User said proceed with the plan.",
                "Exit authority: The assistant selected the plan independently.",
            )
            row["output"] = row["trajectory"][-1]["assistant"]
        self.assert_rejected("grill-multiturn-continuation-exit", mutate)

    def test_quoted_marker_activation(self) -> None:
        self.assert_rejected("grill-quoted-marker-control", lambda row: row["trajectory"][0].update(assistant="Grill status: active\nQuestion: Continue?\nRecommended: Yes.\nAlternatives: Stop."))

    def test_bookkeeping_fields(self) -> None:
        self.assert_rejected("question-first-explicit-grill", lambda row: row["trajectory"][0].update(assistant=row["trajectory"][0]["assistant"] + "\nRound: 1\nFacts checked: none needed"))

    def test_active_after_close(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"].append({"user": "One more thing.", "assistant": "Grill status: active\nQuestion: Reopen?\nRecommended: No.\nAlternatives: Yes."})
            row["output"] = row["trajectory"][-1]["assistant"]
        self.assert_rejected("grill-task-replacement", mutate)

    def test_negation_question_and_continuation_override_exit_keywords(self) -> None:
        pairs = (
            ("Do not implement yet; keep grilling me.", "Exit authority: User said implement."),
            ("Should we proceed, or continue grilling?", "Exit authority: User said proceed."),
            ("不要执行，继续问我。", "Exit authority: 用户要求执行。"),
        )
        for user, assistant in pairs:
            with self.subTest(user=user):
                self.assertFalse(exit_authority_is_grounded(user, assistant))
                def mutate(row: dict, user_text: str = user, authority: str = assistant) -> None:
                    row["trajectory"][-1]["user"] = user_text
                    row["trajectory"][-1]["assistant"] = re.sub(
                        r"(?im)^Exit authority:.*$", authority, row["trajectory"][-1]["assistant"]
                    )
                    row["output"] = row["trajectory"][-1]["assistant"]
                self.assert_rejected("grill-multiturn-continuation-exit", mutate)

    def test_reversible_implementation_question_is_rejected(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][0]["assistant"] = (
                "Grill status: active\nQuestion: Which programming language and how many files should I use?\n"
                "Recommended: TypeScript in two files.\nAlternatives: Python or one file."
            )
        self.assert_rejected("question-first-explicit-grill", mutate)
        self.assertIsNotNone(active_output_violation("Question: Which programming language should I use?"))

    def test_confidence_claim_is_rejected(self) -> None:
        self.assert_rejected(
            "question-first-explicit-grill",
            lambda row: row["trajectory"][0].update(
                assistant=row["trajectory"][0]["assistant"] + "\nConfidence: 90%"
            ),
        )

    def test_fourth_question_exceeds_hard_cap(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"].insert(
                -1,
                {
                    "user": "Keep asking.",
                    "assistant": "Grill status: active\nQuestion: Should another public default change?\nRecommended: No, because compatibility should remain stable.\nAlternatives: Change it, or add an opt-in flag.",
                },
            )
        self.assert_rejected("grill-multiturn-continuation-exit", mutate)

    def test_exhausted_close_cannot_grant_implementation_authority(self) -> None:
        def mutate(row: dict) -> None:
            row["trajectory"][-1]["assistant"] = row["trajectory"][-1]["assistant"].replace(
                "Implementation authority: not granted", "Implementation authority: granted"
            )
            row["output"] = row["trajectory"][-1]["assistant"]
        self.assert_rejected("grill-question-value-stop", mutate)
        self.assertIsNone(
            close_basis(
                "Keep the default.",
                "Grill status: closed\nClose basis: no material user-owned decision remains\nImplementation authority: granted",
            )
        )


if __name__ == "__main__":
    unittest.main()
