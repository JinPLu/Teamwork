#!/usr/bin/env python3
"""Offline tests for the capability-first Codex user-input probe."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from codex_app_server_user_input import (  # noqa: E402
    AppServerProbe,
    ProtocolError,
    SCENARIOS,
    developer_instructions_for_scenario,
    response_for_request,
    validate_request_params,
)


VALID_PARAMS = {
    "itemId": "item-1",
    "threadId": "thread-1",
    "turnId": "turn-1",
    "questions": [
        {
            "id": "host-key-1",
            "header": "Compatibility",
            "question": "Should the public CLI keep a compatibility alias?",
            "options": [
                {
                    "label": "Keep alias",
                    "description": "Existing scripts continue to work while users migrate.",
                },
                {
                    "label": "Break now",
                    "description": "The public command changes immediately.",
                },
            ],
        }
    ],
}


def fake_server_source(params: dict[str, object] = VALID_PARAMS) -> str:
    return f'''\
import json, sys
params = {params!r}
mode = sys.argv[1]
initialized = False
for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    if method == "initialize":
        print(json.dumps({{"id": message["id"], "result": {{}}}}), flush=True)
    elif method == "initialized":
        initialized = True
    elif method == "skills/list":
        raise AssertionError("the capability probe must not mount or inspect a skill")
    elif method == "thread/start":
        assert initialized
        assert message["params"]["approvalPolicy"] == "never"
        assert message["params"]["sandbox"] == "read-only"
        assert message["params"]["ephemeral"] is True
        print(json.dumps({{"id": message["id"], "result": {{"thread": {{"id": "thread-1"}}}}}}), flush=True)
    elif method == "turn/start":
        assert message["params"]["input"][0]["type"] == "text"
        print(json.dumps({{"id": message["id"], "result": {{"turn": {{"id": "turn-1"}}}}}}), flush=True)
        if mode == "zero":
            print(json.dumps({{"method": "item/completed", "params": {{"threadId": "thread-1", "turnId": "turn-1", "item": {{"type": "agentMessage", "text": "Four."}}}}}}), flush=True)
            print(json.dumps({{"method": "turn/completed", "params": {{"threadId": "thread-1", "turn": {{"id": "turn-1", "status": "completed"}}}}}}), flush=True)
        else:
            print(json.dumps({{"id": 99, "method": "item/tool/requestUserInput", "params": params}}), flush=True)
    elif message.get("id") == 99:
        if mode == "wrong-resolution":
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": 99, "threadId": "other-thread"}}}}), flush=True)
        elif mode == "duplicate":
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": 99, "threadId": "thread-1"}}}}), flush=True)
            duplicate = json.loads(json.dumps(params))
            duplicate["itemId"] = "item-2"
            print(json.dumps({{"id": 100, "method": "item/tool/requestUserInput", "params": duplicate}}), flush=True)
        else:
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": 99, "threadId": "thread-1"}}}}), flush=True)
            text = "Should I continue?" if mode == "text-question" else "Compatibility preference recorded."
            print(json.dumps({{"method": "item/completed", "params": {{"threadId": "thread-1", "turnId": "turn-1", "item": {{"type": "agentMessage", "text": text}}}}}}), flush=True)
            print(json.dumps({{"method": "turn/completed", "params": {{"threadId": "thread-1", "turn": {{"id": "turn-1", "status": "completed"}}}}}}), flush=True)
'''


class RequestValidationTests(unittest.TestCase):
    def test_accepts_transport_shape_without_stable_decision_id_rules(self) -> None:
        self.assertEqual(validate_request_params(VALID_PARAMS), [])
        self.assertEqual(
            response_for_request(VALID_PARAMS),
            {"answers": {"host-key-1": {"answers": ["Keep alias"]}}},
        )

    def test_custom_answer_is_returned_for_each_question_key(self) -> None:
        self.assertEqual(
            response_for_request(VALID_PARAMS, "Custom answer"),
            {"answers": {"host-key-1": {"answers": ["Custom answer"]}}},
        )

    def test_rejects_wrong_lifecycle_identity_and_excess_request(self) -> None:
        errors = validate_request_params(
            VALID_PARAMS,
            expected_thread_id="other-thread",
            expected_turn_id="other-turn",
            existing_request_count=1,
        )
        self.assertTrue(any("active thread" in error for error in errors))
        self.assertTrue(any("active turn" in error for error in errors))
        self.assertTrue(any("bounded scenario" in error for error in errors))

    def test_rejects_secret_collection_and_material_timeout(self) -> None:
        invalid = json.loads(json.dumps(VALID_PARAMS))
        invalid["autoResolutionMs"] = 1000
        invalid["questions"][0]["isSecret"] = True
        errors = validate_request_params(invalid)
        self.assertTrue(any("autoResolutionMs" in error for error in errors))
        self.assertTrue(any("credential" in error for error in errors))
        self.assertEqual(
            validate_request_params(invalid, allow_auto_resolution=True),
            ["questions[1] must not collect credential contents"],
        )

    def test_rejects_missing_or_duplicate_option_content(self) -> None:
        invalid = json.loads(json.dumps(VALID_PARAMS))
        invalid["questions"][0]["options"][1]["label"] = "Keep alias"
        invalid["questions"][0]["options"][0]["description"] = ""
        errors = validate_request_params(invalid)
        self.assertTrue(any("description" in error for error in errors))
        self.assertTrue(any("unique" in error for error in errors))

    def test_grill_bound_rejects_multiple_questions_in_one_request(self) -> None:
        invalid = json.loads(json.dumps(VALID_PARAMS))
        second = json.loads(json.dumps(VALID_PARAMS["questions"][0]))
        second["id"] = "host-key-2"
        invalid["questions"].append(second)
        errors = validate_request_params(invalid, max_questions_per_request=1)
        self.assertEqual(errors, ["questions must contain one to 1 items"])


class OfflineLifecycleTests(unittest.TestCase):
    def run_probe(
        self,
        *,
        scenario: str = "protocol",
        mode: str = "native",
        params: dict[str, object] = VALID_PARAMS,
        repeats: int = 1,
        review_dir: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        server = Path(temp.name) / "server.py"
        server.write_text(fake_server_source(params), encoding="utf-8")
        command = [
            sys.executable,
            str(ROOT / "scripts" / "codex_app_server_user_input.py"),
            "--scenario",
            scenario,
            "--model",
            "current-model",
            "--effort",
            "max",
            "--repeats",
            str(repeats),
            "--timeout-seconds",
            "2",
            "--workdir",
            str(ROOT),
            "--server-command",
            json.dumps([sys.executable, str(server), mode]),
        ]
        if review_dir is not None:
            command += ["--review-dir", str(review_dir)]
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )

    def test_scenarios_are_capability_first_and_unmounted(self) -> None:
        self.assertEqual(
            set(SCENARIOS),
            {
                "protocol",
                "ordinary-material",
                "explicit-grill-material",
                "explicit-grill-material-zh",
                "explicit-grill-zero",
                "simple-control",
            },
        )
        self.assertEqual(SCENARIOS["ordinary-material"]["expected_requests"], 1)
        self.assertEqual(SCENARIOS["explicit-grill-material-zh"]["expected_requests"], 1)
        self.assertEqual(
            SCENARIOS["explicit-grill-material-zh"]["max_questions_per_request"], 1
        )
        self.assertTrue(SCENARIOS["explicit-grill-material-zh"]["forbid_text_question"])
        self.assertIn("先问清楚", SCENARIOS["explicit-grill-material-zh"]["prompt"])
        self.assertEqual(SCENARIOS["simple-control"]["expected_requests"], 0)
        rendered = json.dumps(SCENARIOS)
        self.assertNotIn("mounted", rendered)
        self.assertNotIn("oracle", rendered)
        self.assertNotIn("version", rendered)

    def test_only_raw_protocol_probe_cues_the_native_tool(self) -> None:
        self.assertIn(
            "request_user_input",
            developer_instructions_for_scenario("protocol"),
        )
        for scenario in set(SCENARIOS) - {"protocol"}:
            self.assertNotIn(
                "request_user_input",
                developer_instructions_for_scenario(scenario),
            )

    def test_native_request_resolution_and_completion_pass(self) -> None:
        result = self.run_probe()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)["results"][0]
        self.assertEqual(observed["status"], "passed")
        self.assertEqual(observed["observed_item_ids"], ["item-1"])
        self.assertEqual(observed["observed_question_keys"], ["host-key-1"])
        self.assertEqual(observed["resolved_request_count"], 1)
        self.assertEqual(observed["semantic_quality"], "not_evaluated")
        self.assertTrue(observed["native_question_sha256"])
        self.assertNotIn("activation_evidence", observed)

    def test_zero_question_control_passes_without_native_request(self) -> None:
        result = self.run_probe(scenario="simple-control", mode="zero")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)["results"][0]
        self.assertEqual(observed["observed_item_ids"], [])
        self.assertEqual(observed["resolved_request_count"], 0)

    def test_material_scenario_rejects_text_question_duplication(self) -> None:
        result = self.run_probe(scenario="ordinary-material", mode="text-question")
        self.assertEqual(result.returncode, 2)
        observed = json.loads(result.stdout)["results"][0]
        self.assertIn("duplicated", observed["blocker"])
        self.assertTrue(observed["text_question_observed"])

    def test_chinese_explicit_grill_requires_one_native_request_without_text_duplicate(self) -> None:
        passed = self.run_probe(scenario="explicit-grill-material-zh")
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        observed = json.loads(passed.stdout)["results"][0]
        self.assertEqual(observed["resolved_request_count"], 1)

        duplicated = self.run_probe(
            scenario="explicit-grill-material-zh", mode="text-question"
        )
        self.assertEqual(duplicated.returncode, 2)
        blocked = json.loads(duplicated.stdout)["results"][0]
        self.assertIn("duplicated", blocked["blocker"])
        self.assertTrue(blocked["text_question_observed"])

    def test_second_native_request_exceeds_scenario_bound(self) -> None:
        result = self.run_probe(mode="duplicate")
        self.assertEqual(result.returncode, 2)
        self.assertIn("bounded scenario count", result.stdout)

    def test_wrong_resolution_identity_is_rejected(self) -> None:
        result = self.run_probe(mode="wrong-resolution")
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not match one native request", result.stdout)

    def test_invalid_payload_is_hashed_and_review_is_opt_in(self) -> None:
        invalid = json.loads(json.dumps(VALID_PARAMS))
        invalid["questions"][0]["options"] = []
        with tempfile.TemporaryDirectory() as temp:
            review = Path(temp) / "review"
            result = self.run_probe(params=invalid, review_dir=review)
            prose = (review / "repeat-1.txt").read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 2)
        observed = json.loads(result.stdout)["results"][0]
        self.assertTrue(observed["rejected_native_question_sha256"])
        self.assertIn("[rejected native request_user_input]", prose)
        self.assertIn('"options": []', prose)

    def test_default_output_hashes_prose_but_does_not_retain_it(self) -> None:
        result = self.run_probe()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Compatibility preference recorded", result.stdout)
        self.assertNotIn("Should the public CLI", result.stdout)
        observed = json.loads(result.stdout)["results"][0]
        self.assertTrue(observed["agent_message_sha256"])

    def test_review_dir_retains_question_and_prose_but_not_answer_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            review = Path(temp) / "review"
            result = self.run_probe(review_dir=review)
            prose = (review / "repeat-1.txt").read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[native request_user_input]", prose)
        self.assertIn("[assistant item]", prose)
        self.assertIn("Should the public CLI", prose)
        self.assertNotIn('"answers"', prose)

    def test_blocked_repeats_are_recorded_without_hidden_retry(self) -> None:
        result = self.run_probe(mode="duplicate", repeats=2)
        self.assertEqual(result.returncode, 2)
        repeats = json.loads(result.stdout)["results"]
        self.assertEqual(len(repeats), 2)
        self.assertTrue(all(item["status"] == "blocked" for item in repeats))

    def test_handler_rejects_duplicate_protocol_request_id(self) -> None:
        probe = AppServerProbe(["fake"], ROOT, "current", "max", 1)
        sent: list[dict[str, object]] = []
        probe._send = sent.append  # type: ignore[method-assign]
        message = {"id": 99, "method": "item/tool/requestUserInput", "params": VALID_PARAMS}
        self.assertTrue(
            probe._handle_user_input(
                message,
                thread_id="thread-1",
                turn_id="turn-1",
                expected_count=2,
                max_questions_per_request=1,
                allow_auto_resolution=False,
            )
        )
        with self.assertRaisesRegex(ProtocolError, "unique request id"):
            probe._handle_user_input(
                message,
                thread_id="thread-1",
                turn_id="turn-1",
                expected_count=2,
                max_questions_per_request=1,
                allow_auto_resolution=False,
            )


if __name__ == "__main__":
    unittest.main()
