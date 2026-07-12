#!/usr/bin/env python3
"""Integration tests for resumable Teamwork live-eval trajectories."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-teamwork-live-eval.py"
SESSION_ID = "11111111-1111-4111-8111-111111111111"


FAKE_CODEX = f'''#!/usr/bin/env python3
import json
import os
import sys

if sys.argv[1:] == ["--version"]:
    print("codex-fake 1.0")
    raise SystemExit(0)

prompt = sys.stdin.read()
with open(os.environ["TEAMWORK_FAKE_CODEX_LOG"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps({{"argv": sys.argv[1:], "prompt": prompt}}) + "\\n")

is_resume = len(sys.argv) > 2 and sys.argv[1:3] == ["exec", "resume"]
mode = os.environ.get("TEAMWORK_FAKE_MODE", "success")
if is_resume and mode == "resume-failure":
    print("resume failed", file=sys.stderr)
    raise SystemExit(7)
if not is_resume and os.environ.get("TEAMWORK_FAKE_NO_SESSION") != "1":
    print(json.dumps({{"type": "thread.started", "thread_id": "{SESSION_ID}", "model": "gpt-5.6-sol"}}))
if is_resume and mode == "different-session":
    print(json.dumps({{"type": "thread.resumed", "thread_id": "22222222-2222-4222-8222-222222222222", "model": "gpt-5.6-sol"}}))
if not is_resume and mode == "mutation-event":
    print(json.dumps({{"type": "item.completed", "item": {{"type": "file_change", "path": "README.md"}}}}))
message = (
    "Grill status: closed\\nNext route: plan\\nExit authority: User said proceed."
    if is_resume
    else "Grill status: active\\nQuestion: Keep compatibility?\\nRecommended: Yes.\\nAlternatives: Break it or defer it."
)
if is_resume and mode.startswith("bad-authority"):
    message = "Grill status: closed\\nNext route: plan\\nExit authority: The assistant selected the plan independently."
if mode == "bad-behavior":
    message = "I edited the file and finished."
if not is_resume and mode == "low-value-question":
    message = "Grill status: active\\nQuestion: Which programming language and how many files should I use?\\nRecommended: TypeScript in two files.\\nAlternatives: Python or one file."
if not is_resume and mode == "confidence-claim":
    message += "\\nConfidence: 90%"
if not is_resume and mode == "exhausted-zero":
    message = "Grill status: closed\\nClose basis: no material user-owned decision remains\\nImplementation authority: not granted"
if mode != "missing-message":
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": message}}}}))
'''


class LiveEvalRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.temp = Path(self.tempdir.name)
        self.fake = self.temp / "codex-fake"
        self.fake.write_text(FAKE_CODEX, encoding="utf-8")
        self.fake.chmod(0o755)
        self.log = self.temp / "calls.jsonl"
        self.case = self.temp / "case.json"
        self.case.write_text(
            json.dumps(
                {
                    "id": "grill-runner-test",
                    "category": "grill",
                    "prompts": ["grill me", "proceed"],
                    "sandbox": "read-only",
                    "expected_signals": ["active then closed"],
                    "forbidden_signals": ["fallback"],
                    "pilot_only": True,
                }
            ),
            encoding="utf-8",
        )

    def run_runner(self, *, mode: str = "success", no_session: bool = False, final_prompt: str | None = None, prompts: list[str] | None = None) -> tuple[subprocess.CompletedProcess[str], dict]:
        output = self.temp / f"{mode}-{'missing-session' if no_session else 'record'}.jsonl"
        env = os.environ.copy()
        env["TEAMWORK_FAKE_CODEX_LOG"] = str(self.log)
        if no_session:
            env["TEAMWORK_FAKE_NO_SESSION"] = "1"
        env["TEAMWORK_FAKE_MODE"] = mode
        case_path = self.case
        if final_prompt is not None or prompts is not None:
            data = json.loads(self.case.read_text(encoding="utf-8"))
            if prompts is not None:
                data["prompts"] = prompts
            elif final_prompt is not None:
                data["prompts"][-1] = final_prompt
            case_path = self.temp / f"{mode}-case.json"
            case_path.write_text(json.dumps(data), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--arm", "test",
                "--model", "gpt-5.6-sol",
                "--effort", "high",
                "--workdir", str(ROOT),
                "--output", str(output),
                "--cases", str(case_path),
                "--repeats", "1",
                "--timeout-seconds", "10",
                "--codex-bin", str(self.fake),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        self.assertTrue(output.is_file(), completed.stderr or completed.stdout)
        record = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
        return completed, record

    def test_multiturn_uses_explicit_session_resume(self) -> None:
        completed, record = self.run_runner()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        calls = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([call["prompt"] for call in calls], ["grill me", "proceed"])
        self.assertNotIn("--ephemeral", calls[0]["argv"])
        self.assertEqual(
            calls[1]["argv"],
            ["exec", "resume", "--json", "--model", "gpt-5.6-sol", "-c", 'model_reasoning_effort="high"', SESSION_ID, "-"],
        )
        self.assertNotIn("--last", calls[1]["argv"])
        self.assertEqual(record["schema_version"], 2)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["session_id"], SESSION_ID)
        self.assertEqual(record["resolved_model"], "gpt-5.6-sol")
        self.assertEqual(record["model_provenance_status"], "verified")
        self.assertEqual(record["behavioral_status"], "passed")
        self.assertEqual(record["behavior_violations"], [])
        self.assertEqual(record["grill_states"], ["active", "closed"])
        self.assertEqual(len(record["turns"]), 2)
        for index, turn in enumerate(record["turns"], start=1):
            self.assertEqual(turn["turn_index"], index)
            for field in ("argv_shell", "elapsed_seconds", "raw_events", "resolved_model"):
                self.assertIn(field, turn)

    def test_missing_session_fails_without_resume_fallback(self) -> None:
        completed, record = self.run_runner(no_session=True)
        self.assertEqual(completed.returncode, 1)
        calls = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(calls), 1)
        self.assertEqual(record["status"], "failed")
        self.assertEqual(len(record["turns"]), 1)
        self.assertTrue(any("resume was not attempted" in item for item in record["warnings"]))

    def test_resume_failure_propagates(self) -> None:
        completed, record = self.run_runner(mode="resume-failure")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["execution_status"], "failed")
        self.assertEqual(record["status"], "failed")

    def test_different_resume_session_fails(self) -> None:
        completed, record = self.run_runner(mode="different-session")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["status"], "failed")
        self.assertTrue(any("different session id" in item for item in record["warnings"]))

    def test_missing_agent_message_fails(self) -> None:
        completed, record = self.run_runner(mode="missing-message")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["execution_status"], "failed")
        self.assertTrue(any("agent_message" in item for item in record["warnings"]))

    def test_bad_behavior_fails_even_when_commands_succeed(self) -> None:
        completed, record = self.run_runner(mode="bad-behavior")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["execution_status"], "completed")
        self.assertEqual(record["behavioral_status"], "failed")
        self.assertEqual(record["status"], "failed")
        self.assertTrue(record["behavior_violations"])

    def test_mutation_event_before_close_fails_behavior(self) -> None:
        completed, record = self.run_runner(mode="mutation-event")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["behavioral_status"], "failed")
        self.assertTrue(any("forbidden mutation" in item for item in record["behavior_violations"]))

    def test_close_authority_requires_explicit_user_exit_signal(self) -> None:
        completed, record = self.run_runner(mode="bad-authority")
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(record["behavioral_status"], "failed")
        self.assertTrue(any("valid user or exhausted close basis" in item for item in record["behavior_violations"]))

    def test_negated_question_and_continuation_do_not_authorize_close(self) -> None:
        prompts = {
            "bad-authority-negated": "Do not implement yet; keep grilling me.",
            "bad-authority-question": "Should we proceed, or continue grilling?",
            "bad-authority-chinese": "不要执行，继续问我。",
        }
        for mode, prompt in prompts.items():
            with self.subTest(prompt=prompt):
                completed, record = self.run_runner(mode=mode, final_prompt=prompt)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(record["behavioral_status"], "failed")

    def test_low_value_question_and_confidence_claim_fail_behavior(self) -> None:
        for mode in ("low-value-question", "confidence-claim"):
            with self.subTest(mode=mode):
                completed, record = self.run_runner(mode=mode)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(record["behavioral_status"], "failed")

    def test_zero_question_exhausted_close_is_valid_but_grants_no_action(self) -> None:
        completed, record = self.run_runner(
            mode="exhausted-zero",
            prompts=["Grill me on language and file count for a private helper."],
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(record["grill_states"], ["closed"])
        self.assertEqual(record["behavioral_status"], "passed")
        self.assertIn("Implementation authority: not granted", record["final_output"])


if __name__ == "__main__":
    unittest.main()
