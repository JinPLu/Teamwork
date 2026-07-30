#!/usr/bin/env python3
"""Offline tests for the capability-first Codex user-input probe."""

from __future__ import annotations

import json
import os
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
    collaborate_checkpoint_digest,
    collaboration_mode_for_scenario,
    developer_instructions_for_scenario,
    forbidden_generic_collaborate_artifacts,
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

THREE_QUESTION_PARAMS = {
    **VALID_PARAMS,
    "questions": [
        {
            **VALID_PARAMS["questions"][0],
            "id": "compatibility",
            "header": "Compat",
            "question": "How long should compatibility be preserved?",
        },
        {
            **VALID_PARAMS["questions"][0],
            "id": "telemetry",
            "header": "Telemetry",
            "question": "Should telemetry default on?",
            "options": [
                {
                    "label": "Opt in",
                    "description": "Conservative privacy default.",
                },
                {
                    "label": "Default on",
                    "description": "Improves diagnostics at launch.",
                },
            ],
        },
        {
            **VALID_PARAMS["questions"][0],
            "id": "messaging",
            "header": "Message",
            "question": "Which deprecation message should lead?",
            "options": [
                {
                    "label": "Migration",
                    "description": "Lead with upgrade steps.",
                },
                {
                    "label": "Risk",
                    "description": "Lead with compatibility risk.",
                },
            ],
        },
    ],
}


CASE_CLI = ROOT / "scripts" / "discussion-transaction.py"
UPDATED_AT = "2026-07-30T00:00:00+00:00"


def write_empty_case_v2_project(root: Path) -> None:
    memory = root / "docs" / "teamwork"
    memory.mkdir(parents=True, exist_ok=True)
    (memory / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "project": {
                    "name": "Teamwork",
                    "root": ".",
                    "description": "Case-v2 app probe fixture.",
                },
                "active_cases": [],
                "claim_heads": {},
                "aliases": {},
                "recent_cases": [],
                "migration": None,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def case_cli_json(project: Path, *args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(CASE_CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise AssertionError("case CLI did not return an object")
    return payload


def case_inspect(project: Path) -> dict[str, object]:
    return case_cli_json(project, "case-inspect", "--project-root", str(project))


def case_schema(operation: str) -> dict[str, object]:
    return case_cli_json(Path("."), "case-schema", operation)


def case_apply(project: Path, request: dict[str, object]) -> dict[str, object]:
    return case_cli_json(
        project,
        "case-apply",
        "--project-root",
        str(project),
        "--request-json",
        json.dumps(request),
    )


def case_request(
    project: Path,
    operation: str,
    case: dict[str, object] | None = None,
    **extra: object,
) -> dict[str, object]:
    request = case_schema(operation)
    request["expected_revision"] = case_inspect(project)["revision"]
    request["updated_at"] = UPDATED_AT
    if case is not None:
        request["case_id"] = case["case_id"]
        request["expected_manifest_revision"] = case["manifest_revision"]
    request.update(extra)
    return request


def write_case_v2_collaborate_fixture(
    root: Path,
    *,
    include_decision: bool = False,
) -> dict[str, object]:
    write_empty_case_v2_project(root)
    case = case_apply(
        root,
        case_request(
            root,
            "create",
            case_seed="1" * 64,
            title="Case V2 Collaborate",
            task_key="case-v2-collaborate",
            aliases=["case-v2-collaborate"],
            initial_phase="collaborating",
        ),
    )
    case = case_apply(
        root,
        case_request(
            root,
            "collaborate-upsert",
            case,
            source_digest="2" * 64,
            body="## Collaborate\n\n- Case-v2 checkpoint.",
        ),
    )
    if include_decision:
        case = case_apply(
            root,
            case_request(
                root,
                "accept-decision",
                case,
                source_digest="3" * 64,
                body="## Decision\n\n- Accepted case-v2 decision.",
            ),
        )
    # Force the same canonical readback the app probe consumes.
    inspected = case_inspect(root)
    self_case = next(
        row
        for row in inspected["active_cases"]  # type: ignore[index]
        if isinstance(row, dict) and row.get("state", {}).get("case_id") == case["case_id"]
    )
    return {"case": case, "readback": self_case}


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} did not contain an object")
    return payload


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def root_index_path(root: Path) -> Path:
    return root / "docs" / "teamwork" / "index.json"


def manifest_path(root: Path, case_id: str) -> Path:
    return root / "docs" / "teamwork" / "cases" / case_id / "manifest.json"


def collaborate_artifact_path(root: Path, readback: dict[str, object]) -> Path:
    state = readback["state"]
    if not isinstance(state, dict):
        raise AssertionError("readback state missing")
    artifacts = state["artifacts"]
    if not isinstance(artifacts, dict):
        raise AssertionError("readback artifacts missing")
    for row in artifacts.values():
        if (
            isinstance(row, dict)
            and row.get("role") == "collaborate"
            and isinstance(row.get("path"), str)
        ):
            return root / row["path"]
    raise AssertionError("collaborate artifact missing")


def mutate_index_active_case(root: Path, **fields: object) -> None:
    index = read_json(root_index_path(root))
    active = index["active_cases"]
    if not isinstance(active, list) or not active or not isinstance(active[0], dict):
        raise AssertionError("active case missing")
    active[0].update(fields)
    write_json(root_index_path(root), index)


def mutate_manifest_artifact(root: Path, case_id: str, **fields: object) -> None:
    path = manifest_path(root, case_id)
    manifest = read_json(path)
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, dict):
        raise AssertionError("manifest artifacts missing")
    for row in artifacts.values():
        if isinstance(row, dict) and row.get("role") == "collaborate":
            row.update(fields)
            write_json(path, manifest)
            return
    raise AssertionError("collaborate artifact missing")


def fake_server_source(params: dict[str, object] = VALID_PARAMS) -> str:
    return f'''\
import json, sys
params = {params!r}
mode = sys.argv[1]
initialized = False
turns = 0
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
        turns += 1
        assert message["params"]["input"][0]["type"] == "text"
        collaboration = message["params"]["collaborationMode"]
        assert collaboration["mode"] in {{"default", "plan"}}
        assert collaboration["settings"]["model"] == "current-model"
        assert collaboration["settings"]["reasoning_effort"] == "max"
        assert isinstance(collaboration["settings"]["developer_instructions"], str)
        assert collaboration["settings"]["developer_instructions"]
        turn_id = f"turn-{{turns}}"
        print(json.dumps({{"id": message["id"], "result": {{"turn": {{"id": turn_id}}}}}}), flush=True)
        if mode in {{"zero", "prose-question"}}:
            text = "What kind of adoption friction matters most to you?" if mode == "prose-question" else "Four."
            print(json.dumps({{"method": "item/completed", "params": {{"threadId": "thread-1", "turnId": turn_id, "item": {{"type": "agentMessage", "text": text}}}}}}), flush=True)
            print(json.dumps({{"method": "turn/completed", "params": {{"threadId": "thread-1", "turn": {{"id": turn_id, "status": "completed"}}}}}}), flush=True)
        else:
            active = json.loads(json.dumps(params))
            active["turnId"] = turn_id
        if mode == "dependent":
            active["questions"] = [active["questions"][0]]
            active["questions"][0]["id"] = ["global_compatibility", "boundary_rollout", "detail_messaging"][turns - 1]
        print(json.dumps({{"id": 98 + turns, "method": "item/tool/requestUserInput", "params": active}}), flush=True)
    elif message.get("id") in {{99, 100, 101}}:
        turn_id = f"turn-{{turns}}"
        if mode == "wrong-resolution":
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": 99, "threadId": "other-thread"}}}}), flush=True)
        elif mode == "duplicate":
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": 99, "threadId": "thread-1"}}}}), flush=True)
            duplicate = json.loads(json.dumps(params))
            duplicate["itemId"] = "item-2"
            print(json.dumps({{"id": 100, "method": "item/tool/requestUserInput", "params": duplicate}}), flush=True)
        elif mode == "failed-turn":
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": message["id"], "threadId": "thread-1"}}}}), flush=True)
            print(json.dumps({{"method": "turn/completed", "params": {{"threadId": "thread-1", "turn": {{"id": turn_id, "status": "failed", "error": {{"message": "usage limit"}}}}}}}}), flush=True)
        elif mode == "wrong-turn-completed":
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": message["id"], "threadId": "thread-1"}}}}), flush=True)
            print(json.dumps({{"method": "turn/completed", "params": {{"threadId": "thread-1", "turn": {{"id": "other-turn", "status": "completed"}}}}}}), flush=True)
        else:
            print(json.dumps({{"method": "serverRequest/resolved", "params": {{"requestId": message["id"], "threadId": "thread-1"}}}}), flush=True)
            text = "Should I continue?" if mode == "text-question" else "Compatibility preference recorded."
            print(json.dumps({{"method": "item/completed", "params": {{"threadId": "thread-1", "turnId": turn_id, "item": {{"type": "agentMessage", "text": text}}}}}}), flush=True)
            print(json.dumps({{"method": "turn/completed", "params": {{"threadId": "thread-1", "turn": {{"id": turn_id, "status": "completed"}}}}}}), flush=True)
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

    def test_challenge_bound_rejects_multiple_questions_in_one_request(self) -> None:
        invalid = json.loads(json.dumps(VALID_PARAMS))
        second = json.loads(json.dumps(VALID_PARAMS["questions"][0]))
        second["id"] = "host-key-2"
        invalid["questions"].append(second)
        errors = validate_request_params(invalid, max_questions_per_request=1)
        self.assertEqual(errors, ["questions must contain one to 1 items"])

    def test_bounded_batch_accepts_three_and_rejects_four_questions(self) -> None:
        self.assertEqual(
            validate_request_params(THREE_QUESTION_PARAMS, max_questions_per_request=3),
            [],
        )
        invalid = json.loads(json.dumps(THREE_QUESTION_PARAMS))
        fourth = json.loads(json.dumps(VALID_PARAMS["questions"][0]))
        fourth["id"] = "extra"
        invalid["questions"].append(fourth)
        errors = validate_request_params(invalid, max_questions_per_request=3)
        self.assertEqual(errors, ["questions must contain one to 3 items"])


class OfflineLifecycleTests(unittest.TestCase):
    def run_probe(
        self,
        *,
        scenario: str = "collaborate_bounded_native_request",
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
                "collaborate_bounded_native_request",
                "open_brainstorm_prose_question",
                "collaborate_checkpoint_persistence",
                "explicit-challenge-independent-batch",
                "explicit-challenge-dependent-sequence",
            },
        )
        self.assertEqual(
            SCENARIOS["collaborate_bounded_native_request"]["expected_requests"], 1
        )
        self.assertEqual(
            SCENARIOS["open_brainstorm_prose_question"]["expected_requests"], 0
        )
        self.assertTrue(
            SCENARIOS["open_brainstorm_prose_question"]["require_text_question"]
        )
        self.assertEqual(
            SCENARIOS["collaborate_checkpoint_persistence"]["sandbox"],
            "workspace-write",
        )
        self.assertTrue(
            SCENARIOS["collaborate_checkpoint_persistence"][
                "require_collaborate_checkpoint"
            ]
        )
        self.assertEqual(
            SCENARIOS["explicit-challenge-independent-batch"]["max_questions_per_request"],
            3,
        )
        self.assertEqual(SCENARIOS["explicit-challenge-dependent-sequence"]["expected_requests"], 3)
        self.assertEqual(len(SCENARIOS["explicit-challenge-dependent-sequence"]["prompts"]), 3)
        rendered = json.dumps(SCENARIOS)
        self.assertNotIn("mounted", rendered)
        self.assertNotIn("oracle", rendered)
        self.assertNotIn("version", rendered)

    def test_scenarios_do_not_cue_the_native_tool_by_instruction(self) -> None:
        for scenario in SCENARIOS:
            self.assertNotIn(
                "request_user_input",
                developer_instructions_for_scenario(scenario),
            )

    def test_turns_select_an_explicit_collaboration_mode(self) -> None:
        self.assertEqual(
            collaboration_mode_for_scenario(
                "collaborate_bounded_native_request",
                model="current-model",
                effort="max",
            ),
            {
                "mode": "plan",
                "settings": {
                    "model": "current-model",
                    "reasoning_effort": "max",
                    "developer_instructions": (
                        "This is a read-only behavior observation. Follow the user "
                        "request without editing files or performing external actions."
                    ),
                },
            },
        )
        self.assertEqual(
            collaboration_mode_for_scenario(
                "open_brainstorm_prose_question",
                model="current-model",
                effort="max",
            )["mode"],
            "default",
        )

    def test_persistence_probe_allows_only_isolated_workflow_writes(self) -> None:
        instructions = developer_instructions_for_scenario(
            "collaborate_checkpoint_persistence"
        )
        self.assertIn("isolated workspace", instructions)
        self.assertNotIn("Collaborate checkpoint", instructions)
        self.assertNotIn("request_user_input", instructions)

    def test_checkpoint_probe_requires_case_v2_route_and_no_duplicate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture = write_case_v2_collaborate_fixture(root, include_decision=True)
            readback = fixture["readback"]
            self.assertIsInstance(readback, dict)
            self.assertEqual(len(collaborate_checkpoint_digest(root)), 64)
            self.assertEqual(forbidden_generic_collaborate_artifacts(root), [])

            retired = root / "docs" / "teamwork" / "collaborate" / "current.md"
            retired.parent.mkdir(parents=True)
            retired.write_text("Artifact Type: collaborate\n", encoding="utf-8")
            duplicate = (
                root
                / "docs"
                / "teamwork"
                / "workflows"
                / "conclusion"
                / "results"
                / "duplicate.md"
            )
            duplicate.parent.mkdir(parents=True)
            duplicate.write_text("duplicate", encoding="utf-8")
            self.assertEqual(
                forbidden_generic_collaborate_artifacts(root),
                [
                    "docs/teamwork/collaborate/current.md",
                    "docs/teamwork/workflows/conclusion/results/duplicate.md"
                ],
            )

    def test_checkpoint_probe_rejects_missing_or_legacy_record(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            with self.assertRaisesRegex(ProtocolError, "case-inspect failed"):
                collaborate_checkpoint_digest(root)
            current = root / "docs" / "teamwork" / "collaborate" / "current.md"
            current.parent.mkdir(parents=True)
            current.write_text(
                "Artifact Type: collaborate\n"
                '```json\n{"schema_version": 2}\n```\n',
                encoding="utf-8",
            )
            (root / "docs" / "teamwork" / "index.json").write_text(
                json.dumps({"schema_version": 2, "active_cases": [], "recent_cases": []}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ProtocolError, "case-inspect failed"):
                collaborate_checkpoint_digest(root)

    def test_checkpoint_probe_uses_case_inspect_manifest_revision_readback(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            write_case_v2_collaborate_fixture(root)
            mutate_index_active_case(root, manifest_revision="0" * 64)
            with self.assertRaisesRegex(ProtocolError, "case-inspect failed"):
                collaborate_checkpoint_digest(root)

    def test_checkpoint_probe_rejects_noncanonical_manifest_paths(self) -> None:
        for field in ("/tmp/outside-manifest.json", "../outside-manifest.json"):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as name:
                    root = Path(name)
                    write_case_v2_collaborate_fixture(root)
                    outside = root.parent / "outside-manifest.json"
                    outside.write_text('{"outside": true}\n', encoding="utf-8")
                    mutate_index_active_case(root, manifest_path=field)
                    with self.assertRaisesRegex(ProtocolError, "case-inspect failed"):
                        collaborate_checkpoint_digest(root)

    def test_checkpoint_probe_rejects_symlink_manifest_readback(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture = write_case_v2_collaborate_fixture(root)
            case = fixture["case"]
            case_id = str(case["case_id"])
            path = manifest_path(root, case_id)
            outside = root.parent / "outside-valid-manifest.json"
            outside.write_bytes(path.read_bytes())
            path.unlink()
            os.symlink(outside, path)
            with self.assertRaisesRegex(ProtocolError, "case-inspect failed"):
                collaborate_checkpoint_digest(root)

    def test_checkpoint_probe_rejects_unsafe_artifact_paths_before_reading_outside(self) -> None:
        for field in ("/tmp/outside-collaborate.md", "../outside-collaborate.md"):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as name:
                    root = Path(name)
                    fixture = write_case_v2_collaborate_fixture(root)
                    case = fixture["case"]
                    mutate_manifest_artifact(root, str(case["case_id"]), path=field)
                    with self.assertRaisesRegex(ProtocolError, "case-inspect failed"):
                        collaborate_checkpoint_digest(root)

    def test_checkpoint_probe_rejects_symlink_artifact_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture = write_case_v2_collaborate_fixture(root)
            readback = fixture["readback"]
            if not isinstance(readback, dict):
                raise AssertionError("readback missing")
            artifact = collaborate_artifact_path(root, readback)
            outside = root.parent / "outside-collaborate.md"
            outside.write_bytes(artifact.read_bytes())
            artifact.unlink()
            os.symlink(outside, artifact)
            with self.assertRaisesRegex(ProtocolError, "escapes|non-symlink"):
                collaborate_checkpoint_digest(root)

    def test_checkpoint_probe_rejects_artifact_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            fixture = write_case_v2_collaborate_fixture(root)
            readback = fixture["readback"]
            if not isinstance(readback, dict):
                raise AssertionError("readback missing")
            artifact = collaborate_artifact_path(root, readback)
            artifact.write_text(
                artifact.read_text(encoding="utf-8") + "\nTampered bytes.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ProtocolError, "digest does not match"):
                collaborate_checkpoint_digest(root)

    def test_native_request_resolution_and_completion_pass(self) -> None:
        result = self.run_probe(scenario="collaborate_bounded_native_request")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)["results"][0]
        self.assertEqual(observed["status"], "passed")
        self.assertEqual(observed["collaboration_mode"], "plan")
        self.assertEqual(observed["observed_item_ids"], ["item-1"])
        self.assertEqual(observed["observed_question_keys"], ["host-key-1"])
        self.assertEqual(observed["returned_answer_keys"], ["host-key-1"])
        self.assertEqual(observed["observed_turn_ids"], ["turn-1"])
        self.assertEqual(observed["resolved_request_count"], 1)
        self.assertEqual(observed["semantic_quality"], "not_evaluated")
        self.assertTrue(observed["native_question_sha256"])
        self.assertNotIn("activation_evidence", observed)

    def test_open_prose_question_passes_without_native_request(self) -> None:
        result = self.run_probe(
            scenario="open_brainstorm_prose_question",
            mode="prose-question",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)["results"][0]
        self.assertEqual(observed["resolved_request_count"], 0)
        self.assertEqual(observed["collaboration_mode"], "default")

    def test_collaborate_bounded_choice_uses_native_surface_without_text_duplicate(self) -> None:
        result = self.run_probe(scenario="collaborate_bounded_native_request")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)["results"][0]
        self.assertEqual(observed["resolved_request_count"], 1)
        self.assertFalse(observed["text_question_observed"])

    def test_open_brainstorm_requires_one_prose_question_and_no_native_request(self) -> None:
        passed = self.run_probe(
            scenario="open_brainstorm_prose_question",
            mode="prose-question",
        )
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        observed = json.loads(passed.stdout)["results"][0]
        self.assertEqual(observed["resolved_request_count"], 0)
        self.assertTrue(observed["text_question_observed"])

        missing = self.run_probe(
            scenario="open_brainstorm_prose_question",
            mode="zero",
        )
        self.assertEqual(missing.returncode, 2)
        blocker = json.loads(missing.stdout)["results"][0]["blocker"]
        self.assertIn("required open prose question", blocker)

    def test_bounded_collaborate_rejects_text_question_duplication(self) -> None:
        result = self.run_probe(
            scenario="collaborate_bounded_native_request",
            mode="text-question",
        )
        self.assertEqual(result.returncode, 2)
        observed = json.loads(result.stdout)["results"][0]
        self.assertIn("duplicated", observed["blocker"])
        self.assertTrue(observed["text_question_observed"])

    def test_independent_challenge_batch_accepts_three_native_questions(self) -> None:
        result = self.run_probe(
            scenario="explicit-challenge-independent-batch",
            params=THREE_QUESTION_PARAMS,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)["results"][0]
        self.assertEqual(
            observed["observed_question_keys"],
            ["compatibility", "telemetry", "messaging"],
        )
        self.assertEqual(observed["returned_answer_keys"], observed["observed_question_keys"])
        self.assertEqual(observed["resolved_request_count"], 1)

    def test_dependent_challenge_sequence_uses_three_turns_on_one_thread(self) -> None:
        result = self.run_probe(
            scenario="explicit-challenge-dependent-sequence",
            mode="dependent",
            params=THREE_QUESTION_PARAMS,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads(result.stdout)["results"][0]
        self.assertEqual(
            observed["observed_question_keys"],
            ["global_compatibility", "boundary_rollout", "detail_messaging"],
        )
        self.assertEqual(observed["returned_answer_keys"], observed["observed_question_keys"])
        self.assertEqual(observed["observed_turn_ids"], ["turn-1", "turn-2", "turn-3"])
        self.assertEqual(observed["resolved_request_count"], 3)

    def test_second_native_request_exceeds_scenario_bound(self) -> None:
        result = self.run_probe(mode="duplicate")
        self.assertEqual(result.returncode, 2)
        self.assertIn("bounded scenario count", result.stdout)

    def test_wrong_resolution_identity_is_rejected(self) -> None:
        result = self.run_probe(mode="wrong-resolution")
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not match one native request", result.stdout)

    def test_failed_turn_status_is_reported_without_accepting_missing_questions(self) -> None:
        result = self.run_probe(mode="failed-turn")
        self.assertEqual(result.returncode, 2)
        observed = json.loads(result.stdout)["results"][0]
        self.assertIn("turn completed with status 'failed'", observed["blocker"])
        self.assertIn("usage limit", observed["blocker"])
        self.assertIn("turn/completed", observed["events"])

    def test_mismatched_turn_completion_is_rejected_separately(self) -> None:
        result = self.run_probe(mode="wrong-turn-completed")
        self.assertEqual(result.returncode, 2)
        observed = json.loads(result.stdout)["results"][0]
        self.assertIn("turn/completed does not match the active turn", observed["blocker"])
        self.assertIn("turn/completed", observed["events"])

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
