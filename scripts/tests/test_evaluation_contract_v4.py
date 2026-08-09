from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from teamwork_tooling.evaluation.cases import (  # noqa: E402
    selected_cases,
    validate_bound_producer_sources,
    validate_pair_manifest,
)
from teamwork_tooling.evaluation.contracts import EvalError  # noqa: E402
from teamwork_tooling.evaluation.host_matrix import (  # noqa: E402
    HostMatrixError,
    HostProbeError,
    _apply_scenario,
    _codex_session_events,
    _copy_codex_auth,
    classify_case_observation,
    _host_command,
    _missing_host_authentication,
    _retain_candidate,
    _verify_scenario,
    evaluate_agent_output_specificity,
    final_agent_output,
    load_case_manifest,
    load_trajectory_schema,
    observed_agents,
    observed_skills,
    observed_tools,
    route_is_observed,
    run_host_matrix,
    safe_relative,
    validate_candidate,
    validate_record_binding,
    validate_trajectory,
)
from teamwork_tooling.semantic_review import (  # noqa: E402
    SemanticReviewError,
    release_readiness,
)


def trajectory(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": 2,
        "record_type": "teamwork_host_observation",
        "host": "codex",
        "host_executable": "/usr/bin/true",
        "host_version": "codex-cli",
        "profile": "performance-first",
        "case_name": "native-default",
        "started_at": "2026-08-06T00:00:00Z",
        "finished_at": "2026-08-06T00:00:01Z",
        "selected_skill": "native",
        "requested_authority": "read-only",
        "route_observed": True,
        "agent_observations": [],
        "tool_observations": [],
        "final_output": "Clear work stays native and is answered directly.",
        "scenario_verification": "NOT_RUN",
        "candidate_artifact": None,
        "exit_status": 0,
        "status": "PASS",
        "failure_classification": None,
    }
    record.update(overrides)
    return record


def accepted_semantic_evidence() -> dict[str, object]:
    return {
        "status": "PASS",
        "producer_identity": "release-worker",
        "reviewer": {
            "identity": "independent-teamwork-reviewer",
            "role": "reviewer",
            "independent": True,
            "read_actual_candidate": True,
        },
        "actual_candidate": {
            "path": "README.md",
            "content_read": "The current candidate was read in full.",
        },
        "review": "The stated user outcomes are supported by the candidate and evidence.",
        "outcome_rubric": {
            "accurate": "claims match observed behavior",
            "complete": "changed public behavior is covered",
        },
        "verdict": "ACCEPT",
    }


DIRECT_BEHAVIOR_CASES = {
    "collaborate-discoverable-fact",
    "collaborate-bounded-material-preference",
    "collaborate-genuinely-open-question",
    "native-authorized-local-mutation",
    "native-ambiguous-consequential-effect",
    "native-conflicting-typed-claims",
    "review-wrong-outcome-static-green",
    "review-engineering-defect",
    "review-missing-real-path-evidence",
    "review-prose-non-engineering",
}


def release_matrix_module():
    path = ROOT / "scripts/run-teamwork-release-matrix.py"
    spec = importlib.util.spec_from_file_location("teamwork_release_matrix", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RoutingScenarioContractTests(unittest.TestCase):
    def test_live_manifest_declares_codex_release_host_and_adapter_diagnostics(self) -> None:
        manifest = json.loads(
            (ROOT / "evals/teamwork/live-cases/release-matrix.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(["codex"], manifest["release_hosts"])
        cases = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            root=ROOT,
        )
        for case in cases:
            self.assertIn("codex", case["support"])
            self.assertEqual({"codex", "cursor", "claude"}, set(case["support"]))
            self.assertTrue(
                set(case["support"].values())
                <= {"required", "conditional-exact-role"}
            )
            if not case["required_agents"]:
                self.assertEqual("required", case["support"]["codex"])

    def test_release_matrix_hosts_must_match_manifest_release_hosts_exactly(self) -> None:
        module = release_matrix_module()
        manifest = ROOT / "evals/teamwork/live-cases/release-matrix.json"
        declared = module.manifest_release_hosts(manifest)
        self.assertEqual(["codex"], declared)
        module.validate_requested_release_hosts(["codex"], declared)
        for requested in ([], ["cursor"], ["codex", "cursor"], ["cursor", "codex"]):
            with self.subTest(requested=requested), self.assertRaises(HostMatrixError):
                module.validate_requested_release_hosts(requested, declared)

    def test_release_matrix_manifest_requires_declared_release_hosts(self) -> None:
        module = release_matrix_module()
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "cases.json"
            manifest.write_text(
                json.dumps({"schema_version": 3, "cases": []}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HostMatrixError, "release_hosts"):
                module.manifest_release_hosts(manifest)

    def test_release_matrix_support_scope_fails_closed(self) -> None:
        module = release_matrix_module()
        required = {"support": {"codex": "required"}}
        conditional = {"support": {"codex": "conditional-exact-role"}}
        passed = {"status": "PASS", "failure_classification": None}
        missing_role = {
            "status": "UNSUPPORTED",
            "failure_classification": "required-agent-not-observed",
        }
        missing_auth = {
            "status": "UNSUPPORTED",
            "failure_classification": "missing-host-authentication",
        }
        self.assertEqual(
            (True, "required-pass"),
            module.support_result(host="codex", case=required, record=passed),
        )
        self.assertFalse(
            module.support_result(host="codex", case=required, record=missing_role)[0]
        )
        self.assertEqual(
            (True, "conditional-unsupported"),
            module.support_result(
                host="codex", case=conditional, record=missing_role,
            ),
        )
        self.assertFalse(
            module.support_result(
                host="codex", case=conditional, record=missing_auth,
            )[0]
        )

    def test_conditional_missing_role_precedes_unmodified_scenario(self) -> None:
        case = {
            "scenario": "scenario.json",
            "support": {
                "codex": "conditional-exact-role",
                "cursor": "required",
                "claude": "required",
            },
        }
        self.assertEqual(
            ("UNSUPPORTED", "required-agent-not-observed"),
            classify_case_observation(
                case,
                "codex",
                exit_status=0,
                specific=True,
                route_observed=True,
                agents_observed=False,
                verification="FAIL",
                verify_failure="scenario verifier failed",
                specificity_failure=None,
            ),
        )
        self.assertEqual(
            ("FAIL", "scenario verifier failed"),
            classify_case_observation(
                case,
                "codex",
                exit_status=0,
                specific=True,
                route_observed=True,
                agents_observed=True,
                verification="FAIL",
                verify_failure="scenario verifier failed",
                specificity_failure=None,
            ),
        )

    def test_current_scenarios_cover_changed_routes_without_forced_pairs(self) -> None:
        rows = validate_pair_manifest()
        routes = {row["expected_route"] for row in rows}
        self.assertIn("native", routes)
        self.assertIn("teamwork-update", routes)
        self.assertTrue(all(row["platforms"] == ["codex", "cursor", "claude"] for row in rows))

    def test_selected_cases_bind_each_case_to_a_current_semantic_owner(self) -> None:
        rows = selected_cases("all")
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(1, len(row["producers"]))
            validate_bound_producer_sources(row, ROOT)

    def test_empty_owner_override_is_rejected(self) -> None:
        row = selected_cases("all")[0]
        owner = row["producers"][0]["source"]
        with self.assertRaises(EvalError):
            validate_bound_producer_sources(row, ROOT, {owner: ""})

    def test_behavioral_contract_rubric_declares_new_semantic_dimensions(self) -> None:
        rubric = json.loads(
            (ROOT / "evals/teamwork/rubrics/behavioral-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertGreaterEqual(rubric["version"], 8)
        dimensions = {row["name"]: row["description"] for row in rubric["dimensions"]}
        self.assertIn("effect_authority", dimensions)
        self.assertIn("adaptive_questions", dimensions)
        self.assertIn("claim_sensitive_review", dimensions)
        self.assertIn(
            "permission alone does not create authority",
            dimensions["effect_authority"].casefold(),
        )
        self.assertIn("one-question-per-turn", dimensions["adaptive_questions"])
        self.assertIn("lenses cannot compensate", dimensions["claim_sensitive_review"])

    def test_direct_behavior_cases_bind_scenarios_authority_and_exact_roles(self) -> None:
        cases = {
            row["name"]: row
            for row in load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json",
                root=ROOT,
            )
        }
        self.assertTrue(DIRECT_BEHAVIOR_CASES <= set(cases))
        collaborate = {
            "collaborate-discoverable-fact",
            "collaborate-bounded-material-preference",
            "collaborate-genuinely-open-question",
        }
        for name in collaborate:
            case = cases[name]
            self.assertEqual("teamwork-collaborate", case["selected_skill"])
            self.assertEqual([], case["required_agents"])
            self.assertEqual("read-only", case["authority"])
            self.assertEqual(
                "evals/teamwork/live-scenarios/collaborate-question-shapes.json",
                case["scenario"],
            )
            self.assertEqual("required", case["support"]["codex"])

        native_expectations = {
            "native-authorized-local-mutation": ("workspace-write", "authorized-local-mutation.json"),
            "native-ambiguous-consequential-effect": ("read-only", "effect-authority-boundaries.json"),
            "native-conflicting-typed-claims": ("read-only", "effect-authority-boundaries.json"),
        }
        for name, (authority, scenario_name) in native_expectations.items():
            case = cases[name]
            self.assertEqual("native", case["selected_skill"])
            self.assertEqual([], case["required_agents"])
            self.assertEqual(authority, case["authority"])
            self.assertTrue(str(case["scenario"]).endswith(scenario_name))
            self.assertEqual("required", case["support"]["codex"])

        for name in DIRECT_BEHAVIOR_CASES:
            if not name.startswith("review-"):
                continue
            case = cases[name]
            self.assertEqual("teamwork-review", case["selected_skill"])
            self.assertEqual(["reviewer"], case["required_agents"])
            self.assertEqual("read-only", case["authority"])
            self.assertEqual(
                "evals/teamwork/live-scenarios/claim-sensitive-review.json",
                case["scenario"],
            )
            self.assertEqual("required", case["support"]["codex"])

    def test_direct_behavior_scenario_verifiers_cover_fixture_state_only(self) -> None:
        scenario_expectations = {
            "evals/teamwork/live-scenarios/collaborate-question-shapes.json": "PASS",
            "evals/teamwork/live-scenarios/effect-authority-boundaries.json": "PASS",
            "evals/teamwork/live-scenarios/claim-sensitive-review.json": "PASS",
            "evals/teamwork/live-scenarios/authorized-local-mutation.json": "FAIL",
        }
        for scenario_relative, expected in scenario_expectations.items():
            with self.subTest(scenario=scenario_relative):
                with tempfile.TemporaryDirectory() as temporary:
                    target = Path(temporary)
                    _apply_scenario(ROOT, target, scenario_relative)
                    verification, failure = _verify_scenario(target, scenario_relative, ROOT, 10)
                    self.assertEqual(expected, verification)
                    if expected == "PASS":
                        self.assertIsNone(failure)
                    else:
                        self.assertIsNotNone(failure)

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            scenario_relative = "evals/teamwork/live-scenarios/authorized-local-mutation.json"
            _apply_scenario(ROOT, target, scenario_relative)
            (target / "scenario/status.txt").write_text("done\n", encoding="utf-8")
            verification, failure = _verify_scenario(target, scenario_relative, ROOT, 10)
            self.assertEqual("PASS", verification)
            self.assertIsNone(failure)


class InstalledHostObservationTests(unittest.TestCase):
    def test_release_case_manifest_uses_outcomes_not_marker_counts(self) -> None:
        rows = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json", root=ROOT
        )
        self.assertGreaterEqual(len(rows), 1)
        self.assertTrue(all(row["expected_outcomes"] for row in rows))
        self.assertTrue(all("markers" not in row and "required_roles" not in row for row in rows))
        self.assertTrue(all(isinstance(row["required_agents"], list) for row in rows))
        names = {row["name"] for row in rows}
        self.assertIn("debug-evidence-sized-hypotheses", names)
        self.assertIn("update-agent-bootstrap-resume", names)

    def test_case_filter_selects_declared_names(self) -> None:
        rows = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"independent-review"},
            root=ROOT,
        )
        self.assertEqual(["independent-review"], [row["name"] for row in rows])
        with self.assertRaises(HostMatrixError):
            load_case_manifest(
                ROOT / "evals/teamwork/live-cases/release-matrix.json",
                {"not-declared"},
                root=ROOT,
            )

    def test_candidate_validation_uses_current_regular_surfaces(self) -> None:
        result = validate_candidate(ROOT)
        self.assertEqual(str(ROOT.resolve()), result["root"])
        self.assertIn("policy/teamwork-global.md", result["surfaces"])
        self.assertNotIn("manifest", result)

    def test_safe_relative_rejects_escape_and_absolute_paths(self) -> None:
        self.assertEqual("docs/teamwork/index.json", safe_relative("docs/teamwork/index.json"))
        for value in ("../outside", "/absolute", "a/../b", "a\\b"):
            with self.subTest(value=value), self.assertRaises(HostMatrixError):
                safe_relative(value)

    def test_scenario_application_accepts_existing_empty_temporary_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            _apply_scenario(
                ROOT,
                target,
                "evals/teamwork/live-scenarios/debug-direct-cause.json",
            )
            self.assertTrue((target / "scenario/failure.txt").is_file())

    def test_codex_auth_copy_is_limited_to_one_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as source_raw, tempfile.TemporaryDirectory() as target_raw:
            source = Path(source_raw)
            target = Path(target_raw)
            (source / "auth.json").write_text("private fixture", encoding="utf-8")
            (source / "config.toml").write_text("must not copy", encoding="utf-8")
            self.assertTrue(_copy_codex_auth(source, target))
            self.assertEqual(
                "private fixture",
                (target / ".codex/auth.json").read_text(encoding="utf-8"),
            )
            self.assertFalse((target / ".codex/config.toml").exists())

    def test_codex_host_command_persists_isolated_session_for_agent_evidence(self) -> None:
        argv, _version = _host_command(
            "codex",
            "codex",
            ROOT,
            "Inspect the failure.",
            "read-only",
            "gpt-5.6-sol",
            "high",
        )
        self.assertNotIn("--ephemeral", argv)
        self.assertIn("--json", argv)

    def test_codex_session_events_are_read_only_from_isolated_session_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            session = home / ".codex/sessions/2026/08/06/rollout.jsonl"
            session.parent.mkdir(parents=True)
            session.write_text(
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "custom_tool_call",
                            "name": "spawn_agent",
                            "call_id": "call-debugger",
                            "arguments": json.dumps(
                                {"task_name": "causal_check", "agent_type": "teamwork_debugger"}
                            ),
                        },
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "sub_agent_activity",
                            "kind": "started",
                            "event_id": "call-debugger",
                            "agent_path": "/root/causal_check",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            events = _codex_session_events(home)
            self.assertEqual(["debugger"], observed_agents(events))

    def test_trajectory_accepts_observation_shape_and_binding(self) -> None:
        schema = load_trajectory_schema(ROOT / "evals/teamwork/schemas/host-trajectory.schema.json")
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"native-default"},
            root=ROOT,
        )[0]
        record = trajectory()
        validate_trajectory(record, schema)
        validate_record_binding(record, case, schema, ROOT)

    def test_trajectory_rejects_unknown_fields_and_wrong_case_binding(self) -> None:
        with self.assertRaises(HostMatrixError):
            validate_trajectory(trajectory(extra="ceremony"))
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"native-default"},
            root=ROOT,
        )[0]
        with self.assertRaises(HostMatrixError):
            validate_record_binding(trajectory(case_name="another"), case, {}, ROOT)

    def test_pass_trajectory_rejects_contradictory_evidence(self) -> None:
        contradictions = (
            {"host_executable": None},
            {"route_observed": False},
            {"scenario_verification": "FAIL"},
            {"exit_status": 9},
            {"final_output": ""},
            {"failure_classification": "claimed failure"},
        )
        for overrides in contradictions:
            with self.subTest(overrides=overrides), self.assertRaises(HostMatrixError):
                validate_trajectory(trajectory(**overrides))

    def test_conditional_unsupported_read_boundary_fails_closed(self) -> None:
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"update-readiness"},
            root=ROOT,
        )[0]
        base = {
            "case_name": case["name"],
            "selected_skill": case["selected_skill"],
            "requested_authority": case["authority"],
            "status": "UNSUPPORTED",
            "failure_classification": "required-agent-not-observed",
            "exit_status": 0,
            "route_observed": True,
            "final_output": "The exact Explorer role was not observed.",
            "agent_observations": [],
        }
        validate_record_binding(trajectory(**base), case, {}, ROOT)
        contradictions = (
            {"agent_observations": ["explorer"]},
            {"route_observed": False},
            {"exit_status": None},
            {"final_output": ""},
        )
        for overrides in contradictions:
            with self.subTest(overrides=overrides), self.assertRaises(HostMatrixError):
                validate_record_binding(
                    trajectory(**(base | overrides)), case, {}, ROOT,
                )

        scenario_case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"writer-typed-document"},
            root=ROOT,
        )[0]
        scenario_record = trajectory(**(
            base
            | {
                "case_name": scenario_case["name"],
                "selected_skill": scenario_case["selected_skill"],
                "requested_authority": scenario_case["authority"],
                "scenario_verification": "FAIL",
                "candidate_artifact": None,
            }
        ))
        with self.assertRaisesRegex(HostMatrixError, "retain its actual candidate"):
            validate_record_binding(scenario_record, scenario_case, {}, ROOT)

    def test_release_matrix_reads_current_case_name_field(self) -> None:
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"native-default"},
            root=ROOT,
        )[0]
        schema = load_trajectory_schema(ROOT / "evals/teamwork/schemas/host-trajectory.schema.json")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "slice.jsonl"
            path.write_text(json.dumps(trajectory()) + "\n", encoding="utf-8")
            rows = release_matrix_module().read_records(
                path,
                host="codex",
                profile="performance-first",
                cases={case["name"]: case},
                schema=schema,
            )
        self.assertEqual(["native-default"], [row["case_name"] for row in rows])

    def test_release_matrix_refuses_a_self_contradictory_pass(self) -> None:
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"native-default"},
            root=ROOT,
        )[0]
        schema = load_trajectory_schema(ROOT / "evals/teamwork/schemas/host-trajectory.schema.json")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "slice.jsonl"
            path.write_text(
                json.dumps(trajectory(route_observed=False, exit_status=9, final_output="")) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(HostMatrixError):
                release_matrix_module().read_records(
                    path,
                    host="codex",
                    profile="performance-first",
                    cases={case["name"]: case},
                    schema=schema,
                )

    def test_scenario_pass_retains_the_actual_candidate_for_review(self) -> None:
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"writer-typed-document"},
            root=ROOT,
        )[0]
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary)
            scenario = output_root / "scenario"
            document = scenario / "docs/teamwork/plans/plan.md"
            document.parent.mkdir(parents=True)
            document.write_text("# Retained plan\n", encoding="utf-8")
            output = output_root / "host.jsonl"
            artifact = _retain_candidate(scenario, output, case["name"], 1)
            record = trajectory(
                case_name=case["name"],
                selected_skill=case["selected_skill"],
                requested_authority=case["authority"],
                agent_observations=["planner", "writer"],
                scenario_verification="PASS",
                candidate_artifact=artifact,
            )
            validate_record_binding(record, case, {}, output_root)
            self.assertEqual(
                "# Retained plan\n",
                (output_root / artifact / "docs/teamwork/plans/plan.md").read_text(encoding="utf-8"),
            )

    def test_final_output_prefers_assistant_content_and_tool_list_is_observed(self) -> None:
        events = [
            {"type": "tool_call", "tool_name": "read_file", "content": "ignored"},
            {"type": "assistant", "content": [{"type": "text", "text": "Observed final answer."}]},
        ]
        self.assertEqual("Observed final answer.", final_agent_output(events))
        self.assertEqual(["read_file"], observed_tools(events))

    def test_final_output_excludes_prompt_reasoning_commands_and_tool_blocks(self) -> None:
        events = [
            {"type": "thread.started", "prompt": "teamwork-review echoed from the prompt"},
            {
                "type": "item.completed",
                "item": {"type": "reasoning", "text": "private reasoning must not become an answer"},
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "pytest",
                    "aggregated_output": "42 tests passed",
                },
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "name": "read", "input": {"path": "candidate.txt"}},
                        {"type": "text", "text": "The actual candidate lacks test evidence, so revise."},
                    ],
                },
            },
        ]
        self.assertEqual(
            "The actual candidate lacks test evidence, so revise.",
            final_agent_output(events, raw_stdout="prompt and tool transcript"),
        )
        self.assertEqual("", final_agent_output(events[:3], raw_stdout="42 tests passed"))

    def test_route_observation_requires_skill_read_and_rejects_prompt_echo(self) -> None:
        prompt_echo = [{"type": "thread.started", "prompt": "Use teamwork-debug now"}]
        self.assertFalse(route_is_observed(prompt_echo, "teamwork-debug"))
        skill_read = [
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "sed -n '1,220p' /tmp/home/.agents/skills/teamwork-debug/SKILL.md",
                },
            }
        ]
        self.assertEqual(["teamwork-debug"], observed_skills(skill_read))
        self.assertTrue(route_is_observed(skill_read, "teamwork-debug"))
        self.assertFalse(route_is_observed(skill_read, "native"))

        claude_or_cursor_read = [
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Read",
                            "input": {"file_path": "/tmp/home/.claude/skills/teamwork-debug/SKILL.md"},
                        }
                    ],
                },
            }
        ]
        self.assertEqual(["teamwork-debug"], observed_skills(claude_or_cursor_read))
        self.assertTrue(route_is_observed(claude_or_cursor_read, "teamwork-debug"))

    def test_required_agent_binding_uses_child_start_identity(self) -> None:
        event = {"type": "agent.started", "agent_type": "teamwork-writer"}
        self.assertEqual(["writer"], observed_agents([event]))
        codex_event = {
            "type": "event_msg",
            "payload": {
                "type": "sub_agent_activity",
                "kind": "started",
                "agent_thread_id": "child",
                "agent_path": "/root/writer",
            },
        }
        codex_spawn = {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "spawn_agent",
                "call_id": "call-writer",
                "arguments": json.dumps(
                    {"task_name": "document_record", "agent_type": "teamwork_writer"}
                ),
            },
        }
        codex_event["payload"]["event_id"] = "call-writer"
        claude_event = {
            "type": "system",
            "subtype": "hook_response",
            "hook_name": "SubagentStart",
            "hook_input": {"agent_type": "teamwork-writer"},
        }
        self.assertEqual([], observed_agents([codex_event]))
        self.assertEqual(["writer"], observed_agents([codex_spawn, codex_event]))
        self.assertEqual(["writer"], observed_agents([claude_event]))
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"writer-typed-document"},
            root=ROOT,
        )[0]
        record = trajectory(
            case_name=case["name"],
            selected_skill=case["selected_skill"],
            requested_authority=case["authority"],
            agent_observations=["writer"],
        )
        with self.assertRaisesRegex(HostMatrixError, "required Agent observations"):
            validate_record_binding(record, case, {}, ROOT)

    def test_direct_reviewer_cases_require_observed_exact_reviewer(self) -> None:
        case = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/release-matrix.json",
            {"review-missing-real-path-evidence"},
            root=ROOT,
        )[0]
        base = {
            "case_name": case["name"],
            "selected_skill": case["selected_skill"],
            "requested_authority": case["authority"],
            "scenario_verification": "PASS",
            "candidate_artifact": "artifact/reviewer-case",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "artifact/reviewer-case").mkdir(parents=True)
            with self.assertRaisesRegex(HostMatrixError, "required Agent observations"):
                validate_record_binding(trajectory(**base), case, {}, root)

            validate_record_binding(
                trajectory(**(base | {"agent_observations": ["reviewer"]})),
                case,
                {},
                root,
            )

            with self.assertRaisesRegex(HostMatrixError, "conditional exact-role"):
                validate_record_binding(
                    trajectory(**(
                        base
                        | {
                            "status": "UNSUPPORTED",
                            "failure_classification": "required-agent-not-observed",
                            "agent_observations": [],
                        }
                    )),
                    case,
                    {},
                    root,
                )

    def test_answer_presence_is_language_and_length_neutral(self) -> None:
        self.assertEqual((False, "agent-output-missing"), evaluate_agent_output_specificity({}, "  "))
        self.assertEqual((True, None), evaluate_agent_output_specificity({}, "清楚的工作直接原生完成。"))
        self.assertEqual((True, None), evaluate_agent_output_specificity({}, "Done"))
        self.assertEqual(
            (True, None),
            evaluate_agent_output_specificity({}, "The installed policy keeps clear work native and direct."),
        )

    def test_selected_plan_route_requires_fixture_grounded_executable_plan(self) -> None:
        case = {"name": "selected-plan-route"}
        for output in (
            "I cannot safely produce an executable plan without a populated repository.",
            "1. Update the helper. 2. Run tests. 3. Stop if needed.",
            """I will not provide a plan. `report_tasks.py`, `legacy_index.py`,
`teamwork_index_v4.task_keys`, sorted output, and
`python3 -m unittest discover -s scenario/tests` are the relevant details.
Migration, proof, cleanup, stop, and replan remain someone else's work.""",
            """I refuse to supply an executable plan. `report_tasks.py`,
`teamwork_index_v4.task_keys`, sorted output, `legacy_index.py`, and
`python3 -m unittest discover -s scenario/tests` are all relevant. Stop and replan.""",
            """1. Delete `scenario/src/legacy_index.py` first.
2. Migration is requested for `scenario/src/report_tasks.py` and
`teamwork_index_v4.task_keys` with sorted output.
3. Run `python3 -m unittest discover -s scenario/tests`; stop and replan if it fails.""",
            """1. Migration is requested for `scenario/src/report_tasks.py` and
`teamwork_index_v4.task_keys` with sorted output.
2. Run `python3 -m unittest discover -s scenario/tests`.
3. Delete `scenario/src/legacy_index.py`; stop and replan if it fails.""",
            """1. Important context: `scenario/src/report_tasks.py` should use
`teamwork_index_v4.task_keys` and preserve sorted output.
2. Run `python3 -m unittest discover -s scenario/tests`.
3. Delete `scenario/src/legacy_index.py`; stop and replan if it fails.""",
            """1. Do not edit `scenario/src/report_tasks.py`; retain
`teamwork_index_v4.task_keys` and sorted output.
2. Run `python3 -m unittest discover -s scenario/tests`.
3. Delete `scenario/src/legacy_index.py`; stop and replan if it fails.""",
            """1. Edit `scenario/src/report_tasks.py` to use
`teamwork_index_v4.task_keys` and preserve sorted output.
2. Do not run `python3 -m unittest discover -s scenario/tests`.
3. Delete `scenario/src/legacy_index.py`; stop and replan if it fails.""",
            """1. Edit `scenario/src/report_tasks.py` to use
`teamwork_index_v4.task_keys` and preserve sorted output.
2. Run `python3 -m unittest discover -s scenario/tests`.
3. Do not delete `scenario/src/legacy_index.py`; stop and replan if it fails.""",
            """1. Edit `scenario/src/notreport_tasks.py.bak` to use
`notteamwork_index_v4.not_task_keys` and preserve unsorted output.
2. Run `python3 -m unittest discover -s scenario/tests_extra`.
3. Delete `scenario/src/notlegacy_index.py.bak`; stop and replan if it fails.""",
            """1. Edit `scenario/src/report_tasks.py` to use
`teamwork_index_v4.task_keys` and preserve sorted output.
2. Run `python3 -m unittest discover -s scenario/tests_extra`.
3. Delete `scenario/src/legacy_index.py`; stop and replan if it fails.""",
        ):
            with self.subTest(output=output):
                self.assertEqual(
                    (False, "selected-plan-not-executable"),
                    evaluate_agent_output_specificity(case, output),
                )
        executable = """1. Edit `scenario/src/report_tasks.py`: replace the legacy helper with `teamwork_index_v4.task_keys` while preserving sorted task names.
2. Run exactly `python3 -m unittest discover -s scenario/tests`.
3. Only then delete `scenario/src/legacy_index.py`. Stop and replan if the replacement cannot preserve the stated report behavior."""
        self.assertEqual((True, None), evaluate_agent_output_specificity(case, executable))
        staged_cleanup = """1. Edit scenario/src/report_tasks.py to call teamwork_index_v4.task_keys and preserve sorted output.
2. Before cleanup, run python3 -m unittest discover -s scenario/tests; stop and replan if it fails.
3. After the passing migration proof, delete scenario/src/legacy_index.py."""
        self.assertEqual((True, None), evaluate_agent_output_specificity(case, staged_cleanup))
        proof_with_migration = """1. Migrate scenario/src/report_tasks.py to teamwork_index_v4.task_keys and preserve sorted output; then run python3 -m unittest discover -s scenario/tests.
2. Delete scenario/src/legacy_index.py only after that proof passes.
3. Stop and replan if the proof fails."""
        self.assertEqual((True, None), evaluate_agent_output_specificity(case, proof_with_migration))
        proof_verb = """1. Edit scenario/src/report_tasks.py to use teamwork_index_v4.task_keys and preserve sorted output. Prove the caller migration with python3 -m unittest discover -s scenario/tests.
2. Delete scenario/src/legacy_index.py after that proof passes.
3. Stop and replan if the proof fails."""
        self.assertEqual((True, None), evaluate_agent_output_specificity(case, proof_verb))
        imported_helper = """1. Edit scenario/src/report_tasks.py to import task_keys from teamwork_index_v4 and preserve sorted output.
2. Run python3 -m unittest discover -s scenario/tests before deleting scenario/src/legacy_index.py.
3. Stop and replan if the proof fails; otherwise delete scenario/src/legacy_index.py."""
        self.assertEqual((True, None), evaluate_agent_output_specificity(case, imported_helper))

    def test_host_executable_is_resolved_and_retained_for_host_and_install_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "host"
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "if '--version' in sys.argv:\n"
                "    print('host 1')\n"
                "else:\n"
                "    print(json.dumps({'type': 'assistant', 'content': [{'type': 'text', 'text': 'Direct native response.'}]}))\n",
                encoding="utf-8",
            )
            binary.chmod(0o700)
            installer = root / "installer"
            installer.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            installer.chmod(0o700)
            output = root / "observations.jsonl"
            with patch(
                "teamwork_tooling.evaluation.host_matrix._install_command",
                return_value=[str(installer)],
            ):
                self.assertEqual(
                    0,
                    run_host_matrix(
                        host="cursor", binary=str(binary), profile="performance-first",
                        project_root=ROOT,
                        case_manifest=ROOT / "evals/teamwork/live-cases/release-matrix.json",
                        output=output, repeats=1, timeout_seconds=10, extra={},
                        only_cases={"native-default"},
                    ),
                )
            row = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(str(binary.resolve()), row["host_executable"])

            failing_installer = root / "failing-installer"
            failing_installer.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            failing_installer.chmod(0o700)
            failed_output = root / "install-failure.jsonl"
            with patch(
                "teamwork_tooling.evaluation.host_matrix._install_command",
                return_value=[str(failing_installer)],
            ):
                self.assertEqual(
                    1,
                    run_host_matrix(
                        host="cursor", binary=str(binary), profile="performance-first",
                        project_root=ROOT,
                        case_manifest=ROOT / "evals/teamwork/live-cases/release-matrix.json",
                        output=failed_output, repeats=1, timeout_seconds=10, extra={},
                        only_cases={"native-default"},
                    ),
                )
            failed = json.loads(failed_output.read_text(encoding="utf-8"))
            self.assertEqual(str(binary.resolve()), failed["host_executable"])
            self.assertEqual("isolated-install-failed", failed["failure_classification"])

    def test_host_commands_and_authentication_signals_are_evidence_bound(self) -> None:
        claude, _version = _host_command(
            "claude", "claude", Path("/tmp"), "inspect", "read-only",
            "claude-managed", "claude-managed",
        )
        self.assertIn("--verbose", claude)
        cursor, _version = _host_command(
            "cursor", "cursor-agent", Path("/tmp"), "inspect", "read-only",
            "cursor-managed", "cursor-managed",
        )
        self.assertIn("--sandbox", cursor)
        self.assertIn("--mode", cursor)
        self.assertTrue(
            _missing_host_authentication(
                "cursor", 1,
                "Error: Authentication required. Please run 'agent login' first, or set CURSOR_API_KEY environment variable.\n",
                [],
            )
        )
        self.assertTrue(
            _missing_host_authentication(
                "claude", 1, "", [{"type": "assistant", "error": "authentication_failed"}],
            )
        )
        self.assertFalse(
            _missing_host_authentication(
                "claude", 1,
                "Error: When using --print, --output-format=stream-json requires --verbose",
                [],
            )
        )
        self.assertFalse(_missing_host_authentication("cursor", 1, "arbitrary failure", []))
        self.assertFalse(
            _missing_host_authentication(
                "claude", 0, "", [{"type": "assistant", "error": "authentication_failed"}],
            )
        )

    def test_host_version_probe_fails_typed_for_timeout_or_invalid_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scripts = {
                "slow": "#!/bin/sh\nexec sleep 10\n",
                "nonzero": "#!/bin/sh\nprintf 'broken\\n' >&2\nexit 1\n",
                "empty": "#!/bin/sh\nexit 0\n",
            }
            expected = {
                "slow": "host-version-timeout",
                "nonzero": "host-version-unavailable",
                "empty": "host-version-unavailable",
            }
            for name, body in scripts.items():
                binary = root / name
                binary.write_text(body, encoding="utf-8")
                binary.chmod(0o700)
                with self.subTest(name=name), self.assertRaises(HostProbeError) as raised:
                    _host_command(
                        "cursor", str(binary), root, "inspect", "read-only",
                        "cursor-managed", "cursor-managed", 0.2 if name == "slow" else 10,
                    )
                self.assertEqual(expected[name], raised.exception.classification)

    def test_host_timeout_is_retained_as_a_typed_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "slow-host"
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import sys, time\n"
                "if '--version' in sys.argv:\n"
                "    print('slow-host 1')\n"
                "else:\n"
                "    time.sleep(10)\n",
                encoding="utf-8",
            )
            binary.chmod(0o700)
            fast_install = root / "fast-install"
            fast_install.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fast_install.chmod(0o700)
            output = root / "observation.jsonl"
            with patch(
                "teamwork_tooling.evaluation.host_matrix._install_command",
                return_value=[str(fast_install)],
            ):
                result = run_host_matrix(
                    host="cursor",
                    binary=str(binary),
                    profile="performance-first",
                    project_root=ROOT,
                    case_manifest=ROOT / "evals/teamwork/live-cases/release-matrix.json",
                    output=output,
                    repeats=1,
                    timeout_seconds=2,
                    extra={},
                    only_cases={"native-default"},
                )
            self.assertEqual(1, result)
            row = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("FAIL", row["status"])
            self.assertEqual("host-command-timeout", row["failure_classification"])
            self.assertIsNone(row["exit_status"])
            self.assertIn("timed out", row["final_output"])

    def test_isolated_install_timeout_is_retained_as_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            slow_install = root / "slow-install"
            slow_install.write_text("#!/bin/sh\nexec sleep 10\n", encoding="utf-8")
            slow_install.chmod(0o700)
            output = root / "install-timeout.jsonl"
            with patch(
                "teamwork_tooling.evaluation.host_matrix._install_command",
                return_value=[str(slow_install)],
            ):
                result = run_host_matrix(
                    host="cursor",
                    binary="/bin/true",
                    profile="performance-first",
                    project_root=ROOT,
                    case_manifest=ROOT / "evals/teamwork/live-cases/release-matrix.json",
                    output=output,
                    repeats=1,
                    timeout_seconds=1,
                    extra={},
                    only_cases={"native-default"},
                )
            self.assertEqual(1, result)
            row = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("UNSUPPORTED", row["status"])
            self.assertEqual("isolated-install-timeout", row["failure_classification"])
            self.assertEqual("NOT_RUN", row["scenario_verification"])

    def test_scenario_verifier_timeout_is_typed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = root / "candidate"
            scenario.mkdir()
            slow_verifier = root / "slow-verifier"
            slow_verifier.write_text("#!/bin/sh\nexec sleep 10\n", encoding="utf-8")
            slow_verifier.chmod(0o700)
            spec = root / "scenario.json"
            spec.write_text(
                json.dumps({
                    "schema_version": 2,
                    "files": [],
                    "verification": {"argv": [str(slow_verifier)]},
                }),
                encoding="utf-8",
            )
            verification, failure = _verify_scenario(
                scenario, "scenario.json", root, 0.2,
            )
            self.assertEqual("FAIL", verification)
            self.assertEqual("scenario-verifier-timeout", failure)

    def test_invalid_live_case_shape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text(json.dumps({"schema_version": 2, "cases": [{"name": "partial"}]}), encoding="utf-8")
            with self.assertRaises(HostMatrixError):
                load_case_manifest(path, root=ROOT)

    def test_live_scenario_without_verifier_is_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scenario.json").write_text(
                json.dumps({"schema_version": 2, "files": []}),
                encoding="utf-8",
            )
            manifest = root / "cases.json"
            manifest.write_text(
                json.dumps({
                    "schema_version": 3,
                    "cases": [{
                        "name": "unverified",
                        "prompt": "Inspect the supplied fixture.",
                        "selected_skill": "native",
                        "required_agents": [],
                        "expected_outcomes": ["fixture inspected"],
                        "scenario": "scenario.json",
                        "authority": "read-only",
                        "support": {
                            "codex": "required",
                            "cursor": "required",
                            "claude": "required",
                        },
                    }],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HostMatrixError, "must declare verification argv"):
                load_case_manifest(manifest, root=root)


class ReleaseEvidenceTests(unittest.TestCase):
    def test_all_three_evidence_lanes_are_required(self) -> None:
        result = release_readiness(
            {"structural": "PASS", "behavioral": "PASS", "semantic": accepted_semantic_evidence()}
        )
        self.assertEqual("release-ready", result["status"])
        self.assertEqual({}, result["blockers"])

    def test_plain_semantic_pass_is_not_evidence(self) -> None:
        with self.assertRaises(SemanticReviewError):
            release_readiness({"structural": "PASS", "behavioral": "PASS", "semantic": "PASS"})

    def test_semantic_pass_requires_independence_and_actual_candidate_read(self) -> None:
        self_review = accepted_semantic_evidence()
        self_review["reviewer"] = {
            "identity": "release-worker",
            "role": "reviewer",
            "independent": True,
            "read_actual_candidate": True,
        }
        with self.assertRaises(SemanticReviewError):
            release_readiness({"structural": "PASS", "behavioral": "PASS", "semantic": self_review})

        unread = accepted_semantic_evidence()
        unread["reviewer"] = {
            "identity": "independent-teamwork-reviewer",
            "role": "reviewer",
            "independent": True,
            "read_actual_candidate": False,
        }
        with self.assertRaises(SemanticReviewError):
            release_readiness({"structural": "PASS", "behavioral": "PASS", "semantic": unread})

    def test_unsupported_behavior_remains_a_blocker(self) -> None:
        result = release_readiness(
            {"structural": "PASS", "behavioral": "UNSUPPORTED", "semantic": accepted_semantic_evidence()}
        )
        self.assertEqual("not-release-ready", result["status"])
        self.assertEqual({"behavioral": "UNSUPPORTED"}, result["blockers"])


if __name__ == "__main__":
    unittest.main()
