#!/usr/bin/env python3
"""Focused tests for the capability-first live recorder and grill helpers."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from grill_contract import (  # noqa: E402
    event_class,
    has_legacy_grill_ceremony,
    question_count,
    readonly_event_violations,
    synthetic_event,
)

SPEC = importlib.util.spec_from_file_location(
    "run_teamwork_live_eval", SCRIPTS / "run-teamwork-live-eval.py"
)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def command_event(command: str, event_type: str = "item.completed") -> dict[str, object]:
    return {
        "type": event_type,
        "item": {"type": "command_execution", "command": command},
    }


class GrillContractTests(unittest.TestCase):
    def test_question_count_is_transport_neutral(self) -> None:
        self.assertEqual(question_count("Keep compatibility?"), 1)
        self.assertEqual(question_count("保留兼容性？"), 1)
        self.assertEqual(question_count("A? B? C?"), 3)
        self.assertEqual(question_count("No user decision remains."), 0)

    def test_legacy_packet_fields_are_rejected_without_banning_plain_questions(self) -> None:
        self.assertTrue(has_legacy_grill_ceremony("Grill status: active\nQuestion?"))
        self.assertTrue(has_legacy_grill_ceremony("Decision ID: public_default"))
        self.assertTrue(has_legacy_grill_ceremony("Close reason: exhausted"))
        self.assertFalse(
            has_legacy_grill_ceremony(
                "Should existing scripts keep working? I recommend preserving compatibility."
            )
        )

    def test_raw_payload_claims_do_not_bypass_fail_closed_classification(self) -> None:
        claimed = {"event_class": "read", "read_only": True}
        self.assertEqual(event_class(claimed), "unknown-runtime")
        self.assertTrue(readonly_event_violations([claimed]))

    def test_allowlisted_commands_are_read_only_and_mutations_fail(self) -> None:
        safe = [
            command_event("rg -n request_user_input skills"),
            command_event("sed -n '1,40p' skills/grill-me/SKILL.md"),
            command_event("git diff -- skills/grill-me/SKILL.md"),
        ]
        self.assertEqual(readonly_event_violations(safe), [])
        for command in (
            "touch changed.txt",
            "rm -f changed.txt",
            "rg --pre 'touch /tmp/pwn' pattern .",
            "git diff --output=/tmp/leak",
            "echo x > changed.txt",
        ):
            with self.subTest(command=command):
                self.assertTrue(readonly_event_violations([command_event(command)]))

    def test_synthetic_events_are_test_only_and_unknown_names_fail(self) -> None:
        self.assertEqual(readonly_event_violations([synthetic_event("read")]), [])
        self.assertTrue(readonly_event_violations([synthetic_event("mutation")]))
        with self.assertRaises(ValueError):
            synthetic_event("invented")

    def test_codex_0144_lifecycle_events_are_safe_metadata(self) -> None:
        events = [
            {"type": "thread.started", "thread_id": "thread-1"},
            {"type": "turn.started"},
            {"type": "item.started", "item": {"type": "agent_message", "id": "item-1"}},
            {"type": "item.completed", "item": {"type": "error", "id": "item-2", "message": "redacted"}},
            {"type": "turn.completed", "usage": {"input_tokens": 1}},
        ]
        self.assertEqual(readonly_event_violations(events), [])

    def test_codex_0144_read_command_shapes_remain_fail_closed(self) -> None:
        safe_commands = [
            "/bin/zsh -lc \"nl -ba scripts/eval-teamwork.py | sed -n '1,80p'\"",
            "/bin/zsh -lc \"rg --files | sort | sed -n '1,80p'\"",
            "/bin/zsh -lc \"find . -path './.git' -prune -o -type f -print | sort\"",
            "/bin/zsh -lc \"stat -f '%Sm %N' scripts/validate.sh; git branch --show-current; git remote -v\"",
            "/bin/zsh -lc 'PYTHONDONTWRITEBYTECODE=1 python3 scripts/eval-teamwork.py --split dev'",
            "/bin/zsh -lc \"rg -n Teamwork . 2>/dev/null || true\"",
        ]
        for command in safe_commands:
            with self.subTest(command=command):
                self.assertEqual(
                    readonly_event_violations(
                        [command_event(command, "item.started"), command_event(command)]
                    ),
                    [],
                )
        for command in (
            "find . -delete",
            "sort -o changed.txt README.md",
            "sort -ochanged.txt README.md",
            "sort -Tscratch README.md",
            "python3 -c 'open(\"changed.txt\", \"w\").write(\"x\")'",
            "printf x > changed.txt",
        ):
            with self.subTest(command=command):
                self.assertTrue(readonly_event_violations([command_event(command)]))

    def test_grill_structure_allows_bounded_batch_but_rejects_four_questions(self) -> None:
        two_question_turn = [{"final_output": "Compatibility? Telemetry?", "raw_events": []}]
        self.assertEqual(
            RUNNER.assess_structure(two_question_turn, category="grill", dry_run=False),
            ("passed", []),
        )
        four_question_turn = [{"final_output": "A? B? C? D?", "raw_events": []}]
        status, violations = RUNNER.assess_structure(
            four_question_turn, category="grill", dry_run=False
        )
        self.assertEqual(status, "failed")
        self.assertEqual(violations, ["turn 1 asks more than three textual questions"])

class LiveRecorderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_case(
        self,
        *,
        prompts: list[str] | None = None,
        category: str = "grill",
        extra: dict[str, object] | None = None,
    ) -> Path:
        case: dict[str, object] = {
            "id": "capability-first",
            "category": category,
            "sandbox": "read-only",
            "unscored_annotations": {
                "expected": ["semantic review required"],
                "forbidden": ["workspace mutation"],
            },
        }
        values = prompts or ["Ask the bounded material question batch before acting."]
        if len(values) == 1:
            case["prompt"] = values[0]
        else:
            case["prompts"] = values
        if extra:
            case.update(extra)
        path = self.tmp / "case.json"
        path.write_text(json.dumps(case), encoding="utf-8")
        return path

    def write_fake_codex(
        self,
        *,
        first_text: str = "Should existing scripts keep working?",
        resumed_text: str = "No additional material decision remains.",
        include_session: bool = True,
        resolved_model: str | None = None,
        command: str | None = None,
    ) -> Path:
        script = self.tmp / "codex"
        model_expr = repr(resolved_model)
        script.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json
                import sys

                args = sys.argv[1:]
                if args == ["--version"]:
                    print("codex-cli test")
                    raise SystemExit(0)
                resumed = len(args) >= 2 and args[:2] == ["exec", "resume"]
                requested = args[args.index("--model") + 1] if "--model" in args else "unknown"
                model = {model_expr} or requested
                event = {{"type": "thread.resumed" if resumed else "thread.started", "model": model}}
                if {include_session!r}:
                    event["thread_id"] = "thread-1"
                print(json.dumps(event))
                if {command!r} is not None:
                    print(json.dumps({{"type": "item.completed", "item": {{"type": "command_execution", "command": {command!r}}}}}))
                text = {resumed_text!r} if resumed else {first_text!r}
                print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": text}}}}))
                print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 1, "output_tokens": 1}}}}))
                """
            ),
            encoding="utf-8",
        )
        script.chmod(0o755)
        return script

    def run_cli(
        self,
        case: Path,
        *,
        codex: Path | None = None,
        dry_run: bool = False,
        output_name: str = "output.jsonl",
    ) -> subprocess.CompletedProcess[str]:
        output = self.tmp / output_name
        argv = [
            sys.executable,
            str(SCRIPTS / "run-teamwork-live-eval.py"),
            "--arm",
            "test",
            "--model",
            "gpt-test",
            "--effort",
            "medium",
            "--workdir",
            str(ROOT),
            "--output",
            str(output),
            "--cases",
            str(case),
            "--repeats",
            "1",
            "--timeout-seconds",
            "10",
        ]
        if codex is not None:
            argv.extend(["--codex-bin", str(codex)])
        if dry_run:
            argv.append("--dry-run")
        return subprocess.run(argv, text=True, capture_output=True, check=False)

    def read_record(self, name: str = "output.jsonl") -> dict[str, object]:
        return json.loads((self.tmp / name).read_text(encoding="utf-8"))

    def test_case_schema_has_no_pilot_or_state_machine_field(self) -> None:
        case = self.write_case()
        loaded = RUNNER.load_case(case)
        self.assertNotIn("pilot_only", loaded)
        stale = self.write_case(extra={"pilot_only": True})
        with self.assertRaisesRegex(RUNNER.LiveEvalError, "unknown fields: pilot_only"):
            RUNNER.load_case(stale)

    def test_community_research_case_is_a_supported_live_category(self) -> None:
        case = self.write_case(category="community-research")
        loaded = RUNNER.load_case(case)
        self.assertEqual(loaded["category"], "community-research")

    def test_dry_run_records_provenance_without_claiming_semantics(self) -> None:
        case = self.write_case()
        result = self.run_cli(case, dry_run=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["schema_version"], 5)
        self.assertEqual(record["structural_status"], "not_run")
        self.assertEqual(record["question_counts"], [0])
        self.assertEqual(
            record["config_source"]["semantic_scoring"], "external review required"
        )
        self.assertEqual(record["config_source"]["fallback_policy"], "none")

    def test_multiturn_resume_consumes_every_prompt(self) -> None:
        case = self.write_case(prompts=["Grill me first.", "Keep compatibility."])
        result = self.run_cli(case, codex=self.write_fake_codex())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["prompts_consumed"], 2)
        self.assertEqual(record["prompts_remaining"], 0)
        self.assertEqual(record["question_counts"], [1, 0])
        self.assertEqual(record["structural_status"], "passed")
        self.assertEqual(record["session_id"], "thread-1")

    def test_dependent_sequence_records_one_question_per_turn(self) -> None:
        first = "Must compatibility be preserved?"
        second = "Which rollout window follows that answer?"
        case = self.write_case(prompts=[first, second])
        codex = self.write_fake_codex(first_text=first, resumed_text=second)
        result = self.run_cli(case, codex=codex)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["question_counts"], [1, 1])

    def test_missing_session_stops_before_resume(self) -> None:
        case = self.write_case(prompts=["First", "Second"])
        result = self.run_cli(
            case, codex=self.write_fake_codex(include_session=False)
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["termination_reason"], "missing-session")
        self.assertEqual(record["prompts_consumed"], 1)

    def test_legacy_ceremony_fails_structural_gate(self) -> None:
        case = self.write_case()
        result = self.run_cli(
            case,
            codex=self.write_fake_codex(
                first_text="Grill status: active\nShould compatibility remain?"
            ),
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["structural_status"], "failed")
        self.assertTrue(record["structural_violations"])

    def test_mutating_command_fails_read_only_gate(self) -> None:
        case = self.write_case()
        result = self.run_cli(
            case, codex=self.write_fake_codex(command="touch changed.txt")
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["structural_status"], "failed")

    def test_lightweight_case_rejects_even_a_read_only_code_tool(self) -> None:
        case = self.write_case(category="lightweight")
        result = self.run_cli(
            case, codex=self.write_fake_codex(command="rg -n Teamwork README.md")
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["structural_status"], "failed")
        self.assertTrue(
            any("code/toolchain" in item for item in record["structural_violations"])
        )

    def test_model_mismatch_is_recorded_without_fallback(self) -> None:
        case = self.write_case(category="lightweight")
        result = self.run_cli(
            case, codex=self.write_fake_codex(resolved_model="different-model")
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        record = self.read_record()
        self.assertEqual(record["model_provenance_status"], "mismatch")
        self.assertEqual(record["status"], "unavailable")
        self.assertIn("--model gpt-test", record["argv_shell"])

    def test_existing_output_is_never_overwritten(self) -> None:
        case = self.write_case()
        (self.tmp / "output.jsonl").write_text("keep\n", encoding="utf-8")
        result = self.run_cli(case, dry_run=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.tmp / "output.jsonl").read_text(), "keep\n")


if __name__ == "__main__":
    unittest.main()
