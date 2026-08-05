from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from teamwork_tooling.evaluation.cases import selected_cases, validate_pair_manifest  # noqa: E402
from teamwork_tooling.evaluation.contracts import CANONICAL_ROLES, PUBLIC_SKILL_PATHS  # noqa: E402
from teamwork_tooling.evaluation.host_matrix import (  # noqa: E402
    HostMatrixError,
    _case_profile_expectation_for_role,
    _direct_scenario_evidence,
    _dispatches_bind_case,
    evaluate_agent_output_specificity,
    final_agent_output,
    _host_invocation_observation,
    _host_argv,
    _isolated_install_argv,
    _record_role_identity,
    _trajectory_observations,
    _unsupported_record,
    _validate_case_role_contract,
    load_case_manifest,
    load_trajectory_schema,
    observed_dispatches,
    run_host_matrix,
    sha256_bytes,
    validate_record_binding,
    validate_trajectory,
)
from teamwork_tooling.semantic_review import release_readiness  # noqa: E402


def digest(value):
    if isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def installed_semantic_evidence():
    prompt = "Use installed Review and return evidence-backed findings."
    agent_output = "The retained final output reports an evidence-backed finding."
    rubric = {"required": ["retained output", "independent verdict"], "verdicts": ["PASS", "FAIL"]}
    return {
        "status": "PASS",
        "producer_identity": "installed-host-candidate",
        "reviewer": {
            "identity": "teamwork-reviewer-contract",
            "role": "reviewer",
            "independent": True,
        },
        "verdict": "PASS",
        "prompt": prompt,
        "agent_output": agent_output,
        "rubric": rubric,
        "binding": {
            "prompt_sha256": digest(prompt),
            "agent_output_sha256": digest(agent_output),
            "rubric_sha256": digest(rubric),
        },
    }


class SemanticEvaluationContractTests(unittest.TestCase):
    def test_agent_output_specificity_rejects_empty_and_generic_answers(self) -> None:
        case = {"id": "specificity-empty", "evidence": {"markers": []}}
        self.assertEqual((False, "agent-output-empty"), evaluate_agent_output_specificity(case, " \n "))
        self.assertEqual((False, "agent-output-non-answer"), evaluate_agent_output_specificity(case, "Done"))
        self.assertEqual(
            (False, "agent-output-non-answer"),
            evaluate_agent_output_specificity(case, "Everything is done now"),
        )

    def test_agent_output_specificity_allows_paraphrase_without_configured_phrases(self) -> None:
        case = {"id": "specificity-paraphrase", "evidence": {"markers": ["EVIDENCE_RESEARCH_DEPTH_RELEASE"]}}
        ok, failure = evaluate_agent_output_specificity(
            case,
            "The answer cites authoritative public material and keeps the local canary private.",
        )
        self.assertTrue(ok)
        self.assertIsNone(failure)

    def test_agent_output_specificity_allows_chinese_specific_answer(self) -> None:
        case = {"id": "specificity-chinese", "evidence": {"markers": ["EVIDENCE_RESEARCH_DEPTH_RELEASE"]}}
        ok, failure = evaluate_agent_output_specificity(
            case,
            "已核对公开来源，并说明本地隐私边界保持不泄露。",
        )
        self.assertTrue(ok)
        self.assertIsNone(failure)

    def test_agent_output_specificity_rejects_keyword_stuffed_non_answer(self) -> None:
        case = {"id": "specificity-keywords", "evidence": {"markers": ["EVIDENCE_RESEARCH_DEPTH_RELEASE"]}}
        ok, failure = evaluate_agent_output_specificity(
            case,
            "Official source primary public source EVIDENCE_RESEARCH_DEPTH_RELEASE, but I cannot answer.",
        )
        self.assertFalse(ok)
        self.assertEqual("agent-output-non-answer", failure)
        for refusal in ("I must refuse this request.", "I can't help with that request."):
            with self.subTest(refusal=refusal):
                self.assertEqual(
                    (False, "agent-output-non-answer"),
                    evaluate_agent_output_specificity(case, refusal),
                )

    def test_agent_output_specificity_rejects_chinese_generic_and_refusal_answers(self) -> None:
        case = {"id": "specificity-chinese-non-answer", "evidence": {"markers": []}}
        self.assertEqual(
            (False, "agent-output-non-answer"),
            evaluate_agent_output_specificity(case, "好了"),
        )
        self.assertEqual(
            (False, "agent-output-non-answer"),
            evaluate_agent_output_specificity(case, "信息不足，无法回答。"),
        )
        self.assertEqual(
            (False, "agent-output-non-answer"),
            evaluate_agent_output_specificity(case, "我必须拒绝这个请求。"),
        )
        self.assertEqual(
            (False, "agent-output-non-answer"),
            evaluate_agent_output_specificity(case, "我不能帮助处理这个请求。"),
        )

    def test_final_agent_output_ignores_tool_events(self) -> None:
        events = [
            {"type": "user", "content": "prompt text must not be final"},
            {"type": "tool_call", "tool_name": "bash", "content": "tool marker"},
            {"type": "tool_result", "content": "tool output must not be final"},
            {"type": "agent_message", "content": "first answer"},
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "content": [{"type": "text", "text": "final answer"}]},
            },
        ]
        self.assertEqual("final answer", final_agent_output(events))

    def test_final_agent_output_supports_codex_agent_message_shape(self) -> None:
        events = [
            {"type": "tool_result", "content": "tool output"},
            {"type": "agent_message", "message": "Codex retained final answer."},
        ]
        self.assertEqual("Codex retained final answer.", final_agent_output(events))

    def test_final_agent_output_supports_cursor_assistant_message_shape(self) -> None:
        events = [
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "input": {"text": "ignore tool input"}},
                        {"type": "text", "text": "Cursor retained final answer."},
                    ],
                },
            },
        ]
        self.assertEqual("Cursor retained final answer.", final_agent_output(events))

    def test_final_agent_output_supports_claude_delta_and_terminal_result_shapes(self) -> None:
        delta_only = [
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Claude "}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "delta answer."}},
        ]
        self.assertEqual("Claude delta answer.", final_agent_output(delta_only))

        terminal_preferred = [
            *delta_only,
            {"type": "result", "subtype": "success", "result": "Claude terminal full answer."},
        ]
        self.assertEqual("Claude terminal full answer.", final_agent_output(terminal_preferred))

    def test_final_agent_output_ignores_prompt_and_tool_only_streams(self) -> None:
        events = [
            {"type": "user", "content": "Please answer from the scenario."},
            {"type": "tool_call", "tool_name": "bash", "content": "cat scenario/probe.txt"},
            {"type": "tool_result", "content": "EVIDENCE_TOOL_ONLY"},
        ]
        self.assertEqual("", final_agent_output(events))

    def test_trace_marker_only_in_tool_events_still_needs_agent_output_specificity(self) -> None:
        case = {
            "id": "trace-tool-marker",
            "evidence": {
                "kind": "trace",
                "artifact_path": "unused.jsonl",
                "markers": ["TRACE_TOOL_ONLY_MARKER"],
            },
        }
        events = [{"type": "tool_call", "tool_name": "bash", "content": "TRACE_TOOL_ONLY_MARKER"}]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "records.jsonl"
            direct, artifact, result, failure = _direct_scenario_evidence(
                case=case,
                scenario=root,
                events=events,
                output=output,
                invocation_id="run",
                workspace_before=None,
            )
        self.assertTrue(direct)
        self.assertIsNone(failure)
        self.assertTrue(artifact["path"].endswith("host-trace.jsonl"))
        self.assertTrue(result["path"].endswith("scenario-result.jsonl"))
        self.assertEqual(
            (False, "agent-output-empty"),
            evaluate_agent_output_specificity(case, ""),
        )

    def test_codex_root_observation_binds_to_actual_invocation_argv(self) -> None:
        case = next(
            case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
            if case["id"] == "native-result-minimality"
        )
        argv = _host_argv(
            "codex", ["codex"], Path("/sealed/scenario"),
            "prompt claims --model fake and effort=low", case["authority"],
            "gpt-5.6-sol", "high",
        )
        invocation = _host_invocation_observation("codex", argv)
        self.assertEqual(
            {
                "type": "teamwork.invocation.started",
                "host": "codex",
                "model": "gpt-5.6-sol",
                "model_reasoning_effort": "high",
                "sandbox": "workspace-write",
            },
            invocation,
        )
        observations = _trajectory_observations(
            host="codex", events=[invocation, {"type": "thread.started", "thread_id": "real"}],
            case=case,
        )
        self.assertEqual("gpt-5.6-sol", observations["actual_model"])
        self.assertEqual("high", observations["actual_effort"])
        self.assertEqual("workspace-write", observations["authority"])

    def test_root_invocation_observation_cannot_complete_child_dispatch_evidence(self) -> None:
        case = next(
            case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
            if case["id"] == "external-research-depth-privacy"
        )
        invocation = {
            "type": "teamwork.invocation.started",
            "host": "codex",
            "model": "gpt-5.6-sol",
            "model_reasoning_effort": "high",
            "sandbox": case["authority"],
        }
        incomplete_child = {
            "type": "subagent.started",
            "role": case["required_role"],
            "agent_id": "child-without-model-effort",
        }
        events = [invocation, incomplete_child]
        observations = _trajectory_observations(host="codex", events=events, case=case)
        self.assertEqual("UNSUPPORTED", observations["actual_model"])
        self.assertEqual("UNSUPPORTED", observations["actual_effort"])
        self.assertEqual([], observed_dispatches(events, "codex"))
        self.assertEqual(1, observations["child_start_count"])

    def test_isolated_install_argv_matches_each_host_contract(self) -> None:
        installer = Path("/sealed/candidate/install.sh")
        self.assertEqual(
            [
                str(installer), "--copy", "--no-notifications",
                "--no-managed-codegraph", "--no-managed-gpu-broker",
                "--profile", "performance-first", "codex",
            ],
            _isolated_install_argv(installer, "performance-first", "codex"),
        )
        self.assertEqual(
            [
                str(installer), "--copy", "--no-mcp",
                "--profile", "performance-first", "cursor",
            ],
            _isolated_install_argv(installer, "performance-first", "cursor"),
        )
        self.assertEqual(
            [
                str(installer), "--copy", "--no-notifications",
                "--profile", "performance-first", "claude",
            ],
            _isolated_install_argv(installer, "performance-first", "claude"),
        )

    def test_host_invocation_timeout_writes_fail_record_and_continues(self) -> None:
        role_expectations = {
            host: {
                profile: {
                    role: {"model": "gpt-5.6-sol", "effort": "high"}
                    for role in CANONICAL_ROLES
                }
                for profile in ("performance-first", "cost-first")
            }
            for host in ("codex", "cursor", "claude")
        }
        timeout_case = {
            "id": "timeout-case",
            "selected_skill": "native",
            "required_role": "root",
            "expected_roles": [],
            "authority": "workspace-write",
            "required_tools": ["command_execution"],
            "scenario": "scenarios/timeout.json",
            "evidence": {
                "kind": "trace",
                "artifact_path": "unused-timeout.jsonl",
                "markers": ["TIMEOUT_DIRECT_MARKER"],
            },
            "prompt": "timeout prompt must not become evidence",
            "private_markers": ["TIMEOUT_PRIVATE_MARKER"],
        }
        success_case = {
            "id": "success-case",
            "selected_skill": "native",
            "required_role": "root",
            "expected_roles": [],
            "authority": "workspace-write",
            "required_tools": ["command_execution"],
            "scenario": "scenarios/success.json",
            "evidence": {
                "kind": "trace",
                "artifact_path": "unused-success.jsonl",
                "markers": ["SUCCESS_DIRECT_MARKER"],
            },
            "prompt": "success prompt",
            "private_markers": ["SUCCESS_PRIVATE_MARKER"],
        }

        with tempfile.TemporaryDirectory() as project_name, tempfile.TemporaryDirectory() as tree_name:
            project_root = Path(project_name)
            tree = Path(tree_name)
            (tree / "evals/teamwork/live-cases").mkdir(parents=True)
            (tree / "evals/teamwork/schemas").mkdir(parents=True)
            (tree / "scenarios").mkdir()
            (tree / "install.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (tree / "install.sh").chmod(0o755)
            (tree / "evals/teamwork/live-cases/release-matrix.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "required_roles_per_slice": sorted(CANONICAL_ROLES),
                        "role_expectations": role_expectations,
                        "cases": [timeout_case, success_case],
                    }
                ),
                encoding="utf-8",
            )
            (tree / "evals/teamwork/schemas/host-trajectory.schema.json").write_text(
                (ROOT / "evals/teamwork/schemas/host-trajectory.schema.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            for case in (timeout_case, success_case):
                (tree / case["scenario"]).write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "case_id": case["id"],
                            "private_paths": [],
                            "files": [{"path": "fixture.txt", "content": "seed"}],
                        }
                    ),
                    encoding="utf-8",
                )

            auth = project_root / "auth.json"
            auth.write_text('{"token":"safe-test-token"}\n', encoding="utf-8")
            auth.chmod(0o600)
            output = project_root / "evals/teamwork/outputs/installed/records.jsonl"
            host_runs = 0

            @contextmanager
            def fake_materialize(_project_root, _manifest):
                yield tree

            def fake_run(argv, **kwargs):
                nonlocal host_runs
                argv = [str(item) for item in argv]
                if argv[0].endswith("/install.sh"):
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                if argv[:2] == ["codex", "exec"]:
                    host_runs += 1
                    if host_runs == 1:
                        raise subprocess.TimeoutExpired(
                            argv,
                            timeout=kwargs.get("timeout"),
                            output='{"type":"tool_call","tool_name":"bash"}\npartial stdout kept\n',
                            stderr="partial stderr kept\n",
                        )
                    return subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(
                            '{"type":"tool_call","tool_name":"bash"}\n'
                            '{"type":"item.completed","marker":"SUCCESS_DIRECT_MARKER"}\n'
                            '{"type":"agent_message","content":"SUCCESS_DIRECT_MARKER with concrete final evidence from the host run."}\n'
                        ),
                        stderr="",
                    )
                raise AssertionError(f"unexpected subprocess argv: {argv!r}")

            with (
                patch("teamwork_tooling.evaluation.host_matrix.validate_candidate", return_value={"candidate_tree_oid": "0" * 40}),
                patch("teamwork_tooling.evaluation.host_matrix.materialize_candidate", fake_materialize),
                patch("teamwork_tooling.evaluation.host_matrix._preflight_codex_auth_source", return_value=auth),
                patch("teamwork_tooling.evaluation.host_matrix._host_command_prefix", return_value=(["codex"], "codex-test")),
                patch("teamwork_tooling.evaluation.host_matrix.subprocess.run", side_effect=fake_run),
            ):
                result = run_host_matrix(
                    host="codex",
                    binary="codex",
                    profile="performance-first",
                    project_root=project_root,
                    candidate_manifest=project_root / "candidate.json",
                    case_manifest=project_root / "evals/teamwork/live-cases/release-matrix.json",
                    output=output,
                    repeats=1,
                    timeout_seconds=1,
                    extra={},
                    parent_model="gpt-5.6-sol",
                    parent_effort="high",
                )

            self.assertEqual(1, result)
            self.assertEqual(2, host_runs)
            records = [
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(["timeout-case", "success-case"], [record["case_id"] for record in records])
            self.assertEqual("FAIL", records[0]["status"])
            self.assertEqual("host-timeout", records[0]["failure_classification"])
            self.assertEqual(124, records[0]["exit_status"])
            self.assertNotEqual("UNSUPPORTED", records[0]["status"])
            timeout_trace = (output.parent / records[0]["artifact"]["path"]).read_text(encoding="utf-8")
            self.assertIn("teamwork.invocation.started", timeout_trace)
            self.assertIn("partial stdout kept", timeout_trace)
            self.assertIn("partial stderr kept", timeout_trace)
            self.assertNotIn(timeout_case["prompt"], timeout_trace)
            self.assertEqual("PASS", records[1]["status"])
            self.assertIsNone(records[1]["failure_classification"])
            success_output = (output.parent / records[1]["agent_output"]["path"]).read_text(encoding="utf-8")
            self.assertIn("SUCCESS_DIRECT_MARKER", success_output)

    def test_every_pair_has_positive_and_negative_semantics(self) -> None:
        pairs = validate_pair_manifest()
        self.assertTrue(pairs)
        for pair in pairs:
            self.assertNotEqual(
                pair["positive"]["expected_route"],
                pair["negative"]["expected_route"],
            )
            self.assertTrue(pair["positive"]["prompt"].strip())
            self.assertTrue(pair["negative"]["prompt"].strip())

    def test_public_skills_have_positive_routing_coverage(self) -> None:
        routes = {pair["positive"]["expected_route"] for pair in validate_pair_manifest()}
        self.assertTrue(set(PUBLIC_SKILL_PATHS).issubset(routes))

    def test_selected_cases_are_derived_from_pair_manifest(self) -> None:
        pairs = validate_pair_manifest()
        self.assertEqual(2 * len(pairs), len(selected_cases("all")))
        for split in ("dev", "release"):
            expected = 2 * sum(pair["split"] == split for pair in pairs)
            self.assertEqual(expected, len(selected_cases(split)))

    def test_semantic_cases_do_not_use_digest_as_correctness(self) -> None:
        for case in selected_cases("all"):
            self.assertEqual({"route"}, set(case["expected"]))
            self.assertNotIn("sha256", str(case).casefold())
            self.assertNotIn("digest", str(case).casefold())

    def test_release_matrix_uses_topology_roles_and_manifest_case_length(self) -> None:
        path = ROOT / "evals/teamwork/live-cases/release-matrix.json"
        cases = load_case_manifest(path, root=ROOT)
        self.assertTrue(cases)
        observed_roles = {role for case in cases for role in case["expected_roles"]}
        self.assertEqual(set(CANONICAL_ROLES), observed_roles)
        self.assertTrue({case["selected_skill"] for case in cases} <= {*PUBLIC_SKILL_PATHS, "native"})

    def test_native_controls_are_root_only_without_dispatch_roles(self) -> None:
        cases = {
            case["id"]: case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
        }
        for case_id in ("native-result-minimality", "native-no-child-control"):
            self.assertEqual("native", cases[case_id]["selected_skill"])
            self.assertEqual("root", cases[case_id]["required_role"])
            self.assertEqual([], cases[case_id]["expected_roles"])
            self.assertEqual("root", _record_role_identity(cases[case_id], []))

    def test_root_case_contract_rejects_skills_and_child_roles(self) -> None:
        roles = frozenset(CANONICAL_ROLES)
        with self.assertRaisesRegex(HostMatrixError, "selected_skill=native"):
            _validate_case_role_contract(
                {"id": "bad", "selected_skill": "teamwork-collaborate", "required_role": "root"},
                [],
                roles,
            )
        with self.assertRaisesRegex(HostMatrixError, r"expected_roles=\[\]"):
            _validate_case_role_contract(
                {"id": "bad", "selected_skill": "native", "required_role": "root"},
                ["worker"],
                roles,
            )
        with self.assertRaisesRegex(HostMatrixError, "invalid expected_roles"):
            _validate_case_role_contract(
                {"id": "bad", "selected_skill": "native", "required_role": "worker"},
                [],
                roles,
            )

    def test_root_binding_allows_workspace_tools_and_real_path_evidence(self) -> None:
        case = next(
            case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
            if case["id"] == "native-no-child-control"
        )
        schema = load_trajectory_schema(ROOT / "evals/teamwork/schemas/host-trajectory.schema.json")
        with tempfile.TemporaryDirectory() as temporary:
            slice_root = Path(temporary)
            artifacts = slice_root / "artifacts"
            artifacts.mkdir()
            artifact_bytes = b"native root trace"
            result_bytes = case["evidence"]["markers"][0].encode()
            agent_output_bytes = b"Completed the native result through the real path."
            (artifacts / "trace.txt").write_bytes(artifact_bytes)
            (artifacts / "result.txt").write_bytes(result_bytes)
            (artifacts / "agent-output.txt").write_bytes(agent_output_bytes)
            record = {
                "schema_version": 1,
                "record_type": "teamwork_host_trajectory",
                "host": "codex",
                "host_version": "test",
                "invocation_id": "root-run",
                "arm": "performance-first",
                "started_at": "start",
                "finished_at": "finish",
                "case_id": case["id"],
                "profile": "performance-first",
                "parent_model": "gpt-5.6-sol",
                "parent_effort": "high",
                "selected_skill": "native",
                "role_identity": "root",
                "actual_model": "gpt-5.6-sol",
                "actual_effort": "high",
                "dispatches": [],
                "child_start_count": 0,
                "tool_observations": list(case["required_tools"]),
                "authority_observation": case["authority"],
                "sanitized_input_sha256": sha256_bytes(case["prompt"].encode()),
                "artifact": {
                    "path": "artifacts/trace.txt",
                    "sha256": sha256_bytes(artifact_bytes),
                },
                "result": {
                    "path": "artifacts/result.txt",
                    "sha256": sha256_bytes(result_bytes),
                    "direct_success": True,
                },
                "agent_output": {
                    "path": "artifacts/agent-output.txt",
                    "sha256": sha256_bytes(agent_output_bytes),
                },
                "answer_specificity_success": True,
                "exit_status": 0,
                "status": "PASS",
                "privacy_scan": "PASS",
                "failure_classification": None,
            }
            validate_trajectory(record, schema)
            validate_record_binding(record, case, schema, slice_root)
            record["actual_model"] = "child-model"
            with self.assertRaisesRegex(HostMatrixError, "root no-child control"):
                validate_trajectory(record, schema)

    def test_unknown_or_missing_role_child_starts_still_break_root_control(self) -> None:
        root_case = {
            "id": "root-control",
            "selected_skill": "native",
            "required_role": "root",
            "expected_roles": [],
            "authority": "workspace-write",
        }
        events = (
            {"type": "subagent.started", "role": "default"},
            {"type": "agent.started", "role": "unknown"},
            {"type": "subagent.started"},
        )
        for event in events:
            with self.subTest(event=event):
                observed = _trajectory_observations(
                    host="codex", events=[event], case=root_case,
                )
                self.assertEqual([], observed["roles"])
                self.assertEqual(1, observed["child_start_count"])

        case = next(
            case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
            if case["id"] == "native-no-child-control"
        )
        schema = load_trajectory_schema(ROOT / "evals/teamwork/schemas/host-trajectory.schema.json")
        with tempfile.TemporaryDirectory() as temporary:
            slice_root = Path(temporary)
            artifacts = slice_root / "artifacts"
            artifacts.mkdir()
            marker = case["evidence"]["markers"][0].encode()
            agent_output_bytes = b"Completed the native no-child result through the local path."
            (artifacts / "trace.txt").write_bytes(b"trace")
            (artifacts / "result.txt").write_bytes(marker)
            (artifacts / "agent-output.txt").write_bytes(agent_output_bytes)
            record = {
                "schema_version": 1,
                "record_type": "teamwork_host_trajectory",
                "host": "codex",
                "host_version": "test",
                "invocation_id": "root-child-run",
                "arm": "performance-first",
                "started_at": "start",
                "finished_at": "finish",
                "case_id": case["id"],
                "profile": "performance-first",
                "parent_model": "gpt-5.6-sol",
                "parent_effort": "high",
                "selected_skill": "native",
                "role_identity": "root",
                "actual_model": "gpt-5.6-sol",
                "actual_effort": "high",
                "dispatches": [],
                "child_start_count": 1,
                "tool_observations": list(case["required_tools"]),
                "authority_observation": case["authority"],
                "sanitized_input_sha256": sha256_bytes(case["prompt"].encode()),
                "artifact": {"path": "artifacts/trace.txt", "sha256": sha256_bytes(b"trace")},
                "result": {
                    "path": "artifacts/result.txt",
                    "sha256": sha256_bytes(marker),
                    "direct_success": True,
                },
                "agent_output": {
                    "path": "artifacts/agent-output.txt",
                    "sha256": sha256_bytes(agent_output_bytes),
                },
                "answer_specificity_success": True,
                "exit_status": 0,
                "status": "PASS",
                "privacy_scan": "PASS",
                "failure_classification": None,
            }
            with self.assertRaisesRegex(HostMatrixError, "root no-child control"):
                validate_record_binding(record, case, schema, slice_root)

    def test_cursor_and_claude_root_require_observed_model_and_effort(self) -> None:
        case = next(
            case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
            if case["id"] == "native-no-child-control"
        )
        schema = load_trajectory_schema(ROOT / "evals/teamwork/schemas/host-trajectory.schema.json")
        partial_events = (
            ({"type": "thread.started", "effort": "high"}, "actual_model"),
            ({"type": "thread.started", "model": "observed-parent"}, "actual_effort"),
        )
        for host in ("cursor", "claude"):
            for event, missing_field in partial_events:
                with self.subTest(host=host, missing_field=missing_field):
                    observed = _trajectory_observations(host=host, events=[event], case=case)
                    self.assertEqual("UNSUPPORTED", observed[missing_field])

                    record = _unsupported_record(
                        host, "performance-first", case, "missing-root-observation",
                        parent_model="observed-parent", parent_effort="high",
                    )
                    record.update({
                        "selected_skill": "native",
                        "role_identity": "root",
                        "actual_model": observed["actual_model"],
                        "actual_effort": observed["actual_effort"],
                        "tool_observations": list(case["required_tools"]),
                        "authority_observation": case["authority"],
                        "artifact": {"path": "artifacts/trace", "sha256": "0" * 64},
                        "result": {
                            "path": "artifacts/result", "sha256": "1" * 64,
                            "direct_success": True,
                        },
                        "status": "PASS",
                        "privacy_scan": "PASS",
                    })
                    with self.assertRaisesRegex(HostMatrixError, "root no-child control"):
                        validate_trajectory(record, schema)

    def test_dispatch_binding_uses_actual_child_start_model_and_effort(self) -> None:
        case = next(
            case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
            if case["id"] == "external-research-depth-privacy"
        )
        expected = _case_profile_expectation_for_role(
            case, "codex", "performance-first", "researcher",
        )
        event = {
            "type": "subagent.started",
            "role": "researcher",
            "agent_id": "child-1",
            "model": expected["model"],
            "effort": expected["effort"],
        }
        dispatches = observed_dispatches([event], "codex")
        self.assertEqual(1, len(dispatches))
        self.assertEqual("researcher", dispatches[0]["role"])
        self.assertTrue(
            _dispatches_bind_case(case, "codex", "performance-first", dispatches, 1)
        )

        for field, wrong in (("actual_model", "wrong-model"), ("actual_effort", "wrong-effort")):
            with self.subTest(field=field):
                altered = [{**dispatches[0], field: wrong}]
                self.assertFalse(
                    _dispatches_bind_case(case, "codex", "performance-first", altered, 1)
                )

    def test_incomplete_child_start_never_becomes_dispatch_evidence(self) -> None:
        events = (
            {
                "type": "subagent.started", "role": "default", "agent_id": "child-1",
                "model": "gpt-5.6-terra", "effort": "high",
            },
            {
                "type": "agent.started", "role": "researcher", "agent_id": "child-2",
                "effort": "high",
            },
            {
                "type": "SubagentStart", "role": "researcher",
                "model": "gpt-5.6-terra", "effort": "high",
            },
        )
        for event in events:
            with self.subTest(event=event):
                self.assertEqual([], observed_dispatches([event], "codex"))

    def test_ordinary_collaborate_case_does_not_overdispatch(self) -> None:
        case = next(
            case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
            if case["id"] == "collaborate-evidence-bounded-convergence"
        )
        self.assertEqual("explorer", case["required_role"])
        self.assertEqual(["explorer"], case["expected_roles"])
        self.assertNotIn("strict adversarial challenge", case["prompt"].split("Do not", 1)[0])

    def test_readiness_update_and_strict_challenge_each_dispatch_one_role(self) -> None:
        cases = {
            case["id"]: case
            for case in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
            )
        }
        update = cases["update-prepost-privileged"]
        self.assertEqual("explorer", update["required_role"])
        self.assertEqual(["explorer"], update["expected_roles"])

        challenger = cases["strict-adversarial-challenger"]
        self.assertEqual("teamwork-collaborate", challenger["selected_skill"])
        self.assertEqual("challenger", challenger["required_role"])
        self.assertEqual(["challenger"], challenger["expected_roles"])

    def test_release_runner_has_no_numeric_expected_count_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/run-teamwork-release-matrix.py"), "verify", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("--expected-records", result.stdout)
        self.assertNotIn("--expected-total-records", result.stdout)
        self.assertNotIn("--required-roles-per-slice", result.stdout)
        self.assertNotIn("--codex-arms", result.stdout)

    def test_all_three_host_entrypoints_are_callable(self) -> None:
        for host in ("codex", "cursor", "claude"):
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / f"scripts/run-installed-{host}-teamwork-live-eval.py"),
                    "--help",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, f"{host}: {result.stderr}")

    def test_not_run_required_lane_cannot_be_release_ready(self) -> None:
        result = release_readiness({
            "static": "PASS",
            "installed_semantic": installed_semantic_evidence(),
            "disposable_write": "NOT RUN",
            "dry_run": "PASS",
        })
        self.assertEqual("not-release-ready", result["status"])
        self.assertEqual("NOT RUN", result["blockers"]["disposable_write"])

    def test_all_required_lanes_pass_release_gate(self) -> None:
        result = release_readiness({
            "static": "PASS",
            "installed_semantic": installed_semantic_evidence(),
            "disposable_write": "PASS",
        })
        self.assertEqual("release-ready", result["status"])
        self.assertEqual({}, result["blockers"])
        self.assertEqual("NOT RUN", result["lanes"]["dry_run"])


if __name__ == "__main__":
    unittest.main()
