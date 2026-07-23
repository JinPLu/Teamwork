from __future__ import annotations

import importlib.util
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from teamwork_tooling.evaluation import cases as case_module
from teamwork_tooling.evaluation.cases import selected_cases, validate_bound_producer_sources, validate_case
from teamwork_tooling.evaluation.contracts import (
    CANONICAL_ROLES,
    DESIGN_ADVERSARIAL_REFERENCE_PATH,
    EvalError,
    ROLE_TEMPLATE_PATHS,
)
from teamwork_tooling.evaluation.host_matrix import (
    HostMatrixError,
    LEGACY_V4_C5_ROLES,
    _direct_scenario_evidence,
    _immutable_scenario_hashes,
    _run_scenario_verifier,
    load_case_manifest,
    load_trajectory_schema,
    sha256_file,
    validate_trajectory,
)
from teamwork_tooling.evaluation.sources import validate_role_template_sources, validate_skill_source_contract


def dispatch_for(host: str, role: str, invocation_id: str, model: str, effort: str) -> dict[str, object]:
    base = {
        "host": host,
        "role": role,
        "dispatch_id": f"{invocation_id}-{role}",
        "parent_invocation_id": invocation_id,
        "actual_model": model,
        "actual_effort": effort,
        "requested_model": None,
        "requested_effort": None,
    }
    if host == "codex":
        return {
            **base,
            "selector_kind": "agent_type",
            "agent_type": f"teamwork_{role.replace('-', '_')}",
            "subagent_identity": None,
            "fork_turns": "none",
            "model_override_present": False,
            "effort_override_present": False,
            "observation_source": "codex-product-coordination",
        }
    if host == "claude":
        return {
            **base,
            "selector_kind": "subagent_identity",
            "agent_type": None,
            "subagent_identity": role,
            "fork_turns": None,
            "model_override_present": None,
            "effort_override_present": None,
            "observation_source": "claude-hooks-transcript",
        }
    return {
        **base,
        "selector_kind": "cursor-agent-role",
        "agent_type": None,
        "subagent_identity": role,
        "fork_turns": None,
        "model_override_present": None,
        "effort_override_present": None,
        "observation_source": "cursor-stream-json",
    }


class EvaluationContractV4Tests(unittest.TestCase):
    def test_active_cases_bind_exact_real_producers(self) -> None:
        cases = selected_cases("all")
        self.assertTrue(cases)
        for case in cases:
            self.assertNotIn("target", case)
            self.assertTrue(case["producers"])
            for producer in case["producers"]:
                self.assertTrue((ROOT / producer["source"]).is_file())

    def test_unrelated_existing_target_is_rejected(self) -> None:
        source = ROOT / "evals/teamwork/cases/native-minimal-en.dev.v4.json"
        value = json.loads(source.read_text(encoding="utf-8"))
        value["producers"] = [{"class": "skill", "source": "skills/teamwork-debug/SKILL.md"}]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / source.name
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(EvalError, "producer binding mismatch"):
                validate_case(path, {"behavioral-contracts"})

    def test_native_minimality_binds_root_and_worker_on_all_hosts(self) -> None:
        by_id = {case["id"]: case for case in selected_cases("dev")}
        expected = {"scripts/install/policy.sh"} | {
            ROLE_TEMPLATE_PATHS[host]["worker"] for host in ("codex", "cursor", "claude")
        }
        for case_id in ("native-minimal-en", "native-minimal-zh"):
            self.assertEqual(expected, {item["source"] for item in by_id[case_id]["producers"]})

    def test_mutating_each_rendered_native_owner_fails_the_bound_case(self) -> None:
        case = next(case for case in selected_cases("dev") if case["id"] == "native-quality-proportional-proof")
        case_path = ROOT / "evals/teamwork/cases/native-quality-proportional-proof.dev.v4.json"
        for producer in case["producers"]:
            source_path = producer["source"]
            source = (ROOT / source_path).read_text(encoding="utf-8")
            if producer["class"] == "root-policy":
                mutated = re.sub(r"focused\s+automated\s+regression\s+evidence", "generic evidence", source, count=1)
            else:
                mutated = source.replace("proportional", "uniform").replace("Proportional", "Uniform")
            self.assertNotEqual(source, mutated, source_path)
            with self.subTest(source=source_path), self.assertRaisesRegex(EvalError, "bound producer"):
                validate_bound_producer_sources(case, case_path, {source_path: mutated})

    def test_every_bound_root_skill_role_and_artifact_owner_is_mutation_sensitive(self) -> None:
        """A real producer path is not enough: every bound owner has a checked rule."""

        owners: dict[str, dict[str, object]] = {}
        for case in selected_cases("all"):
            case_path = ROOT / "evals/teamwork/cases" / f"{case['id']}.{case['split']}.v4.json"
            for producer in case["producers"]:
                owners.setdefault(producer["source"], {"case": case, "path": case_path, "class": producer["class"]})
        self.assertTrue(owners)
        for source_path, owner in owners.items():
            source = (ROOT / source_path).read_text(encoding="utf-8")
            producer_class = owner["class"]
            if source_path == DESIGN_ADVERSARIAL_REFERENCE_PATH:
                mutated = source.replace(
                    "Every actual hypothesis gets exactly\n   two fresh Designer critics",
                    "Every actual hypothesis gets one reused Designer critic",
                    1,
                )
            elif producer_class == "root-policy":
                mutated = source.replace("Root alone asks", "Root never asks", 1)
            elif producer_class == "skill":
                mutated = source.replace("Use when", "Apply when", 1)
            elif producer_class == "role-template":
                mutated = source.replace("Mission:", "Objective:", 1)
            elif source_path == "scripts/discussion-transaction.py":
                mutated = source.replace("def inspect_discussion(", "def removed_inspect_discussion(", 1)
            elif source_path == "scripts/init-project-files.py":
                mutated = source.replace("_recover_init_transaction", "removed_recovery")
            elif source_path == "scripts/check-update.sh":
                mutated = re.sub("readiness", "freshness", source, flags=re.IGNORECASE)
            else:
                self.fail(f"uncovered producer mutation: {source_path}")
            self.assertNotEqual(source, mutated, source_path)
            with self.subTest(source=source_path), self.assertRaises(EvalError):
                validate_bound_producer_sources(owner["case"], owner["path"], {source_path: mutated})

    def test_adversarial_cases_bind_the_reference_and_reject_core_inversions(self) -> None:
        case_ids = {
            "design-adversarial-activation-en",
            "design-adversarial-activation-zh",
            "release-design-adversarial-boundary",
        }
        cases = {case["id"]: case for case in selected_cases("all") if case["id"] in case_ids}
        self.assertEqual(case_ids, set(cases))
        for case in cases.values():
            self.assertIn(
                DESIGN_ADVERSARIAL_REFERENCE_PATH,
                {producer["source"] for producer in case["producers"]},
            )

        source = (ROOT / DESIGN_ADVERSARIAL_REFERENCE_PATH).read_text(encoding="utf-8")
        case = cases["design-adversarial-activation-en"]
        case_path = ROOT / "evals/teamwork/cases/design-adversarial-activation-en.dev.v4.json"
        mutations = (
            (
                "selects it automatically or an\nexplicit adversarial override",
                "runs only after explicit adversarial wording",
            ),
            (
                "do not\nrequest confirmation",
                "request confirmation",
            ),
            (
                "Every actual hypothesis gets exactly\n   two fresh Designer critics",
                "Every actual hypothesis gets one reused Designer critic",
            ),
            (
                "Converge only when both final auditors return `PASS`",
                "Converge when either final auditor returns `PASS`",
            ),
            (
                "Using the final unit of `B` is valid closure",
                "Using the final unit of `B` is budget exhaustion",
            ),
        )
        for before, after in mutations:
            mutated = source.replace(before, after, 1)
            self.assertNotEqual(source, mutated, before)
            with self.subTest(before=before), self.assertRaises(EvalError):
                validate_bound_producer_sources(
                    case,
                    case_path,
                    {DESIGN_ADVERSARIAL_REFERENCE_PATH: mutated},
                )

    def test_universal_fallback_inversion_fails_paired_case(self) -> None:
        case = next(case for case in selected_cases("dev") if case["id"] == "native-quality-accepted-fallback")
        source_path = "scripts/install/policy.sh"
        source = (ROOT / source_path).read_text(encoding="utf-8")
        mutated = re.sub(r"Do\s+not\s+add\s+an\s+unrequested\s+wrapper", "Never add any fallback", source, count=1)
        self.assertNotEqual(source, mutated)
        with self.assertRaisesRegex(EvalError, "conditional wrapper/fallback"):
            validate_bound_producer_sources(case, ROOT / "evals/teamwork/cases/native-quality-accepted-fallback.dev.v4.json", {source_path: mutated})

    def test_all_six_native_quality_pairs_have_both_controls(self) -> None:
        dimensions = set()
        for case in selected_cases("dev"):
            if case["expected"]["scenario"] == "engineering-quality":
                dimensions.add(case["pair"]["dimension"])
                self.assertTrue(case["pair"]["positive"])
                self.assertTrue(case["pair"]["negative"])
        self.assertEqual(
            {"canonical-owner", "accepted-fallback", "proportional-proof", "cohesive-structure", "scope-residue", "result-stop"},
            dimensions,
        )

    def test_legacy_release_manifest_is_exact_and_maps_legacy_roles(self) -> None:
        manifest = ROOT / "evals/teamwork/live-cases/v4-release-matrix.json"
        cases = load_case_manifest(manifest)
        self.assertEqual(13, len(cases))
        self.assertEqual(set(LEGACY_V4_C5_ROLES), {role for case in cases for role in case["expected_roles"]})
        self.assertNotIn("writer", {role for case in cases for role in case["expected_roles"]})

    def test_c5_case_contract_freezes_the_exact_104_record_matrix(self) -> None:
        contract_path = ROOT / "evals/teamwork/manifests/v4.1.0-teamwork-c5-cases.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract_cases = load_case_manifest(contract_path)
        release_cases = load_case_manifest(
            ROOT / "evals/teamwork/live-cases/v4-release-matrix.json"
        )
        self.assertEqual("teamwork-4.1.0-c5", contract["candidate_id"])
        self.assertEqual(13, contract["expected_records_per_output"])
        self.assertEqual(104, contract["expected_total_records"])
        self.assertEqual(
            [
                "performance-first-root-gpt55-low",
                "performance-first-root-gpt55-high",
                "cost-first-root-gpt55-low",
                "cost-first-root-gpt55-high",
            ],
            contract["codex_arms"],
        )
        self.assertEqual(
            [case["id"] for case in release_cases],
            [case["id"] for case in contract_cases],
        )

    def test_codex_live_matrix_uses_the_role_optimized_profile_expectations(self) -> None:
        cases = load_case_manifest(ROOT / "evals/teamwork/live-cases/v4-release-matrix.json")
        matrix = cases[0]["role_expectations"]["codex"]
        self.assertEqual(
            {
                "researcher": {"model": "gpt-5.5", "effort": "high"},
                "explorer": {"model": "gpt-5.5", "effort": "high"},
                "debugger": {"model": "gpt-5.5", "effort": "high"},
                "designer": {"model": "gpt-5.6-sol", "effort": "high"},
                "planner": {"model": "gpt-5.5", "effort": "high"},
                "worker": {"model": "gpt-5.5", "effort": "high"},
                "plan-reviewer": {"model": "gpt-5.6-sol", "effort": "high"},
                "reviewer": {"model": "gpt-5.6-sol", "effort": "max"},
            },
            matrix["performance-first"],
        )
        self.assertEqual(
            {
                "researcher": {"model": "gpt-5.5", "effort": "medium"},
                "explorer": {"model": "gpt-5.5", "effort": "medium"},
                "debugger": {"model": "gpt-5.5", "effort": "medium"},
                "designer": {"model": "gpt-5.6-sol", "effort": "medium"},
                "planner": {"model": "gpt-5.5", "effort": "medium"},
                "worker": {"model": "gpt-5.5", "effort": "medium"},
                "plan-reviewer": {"model": "gpt-5.6-sol", "effort": "high"},
                "reviewer": {"model": "gpt-5.6-sol", "effort": "high"},
            },
            matrix["cost-first"],
        )

    def test_grill_public_eval_contract_allows_the_major_transaction_route(self) -> None:
        rubric = json.loads(
            (ROOT / "evals/teamwork/rubrics/behavioral-contracts.json").read_text(encoding="utf-8")
        )
        dimension = next(
            item for item in rubric["dimensions"] if item["name"] == "grill_authority_and_persistence"
        )
        description = dimension["description"].casefold()
        readme = (ROOT / "evals/teamwork/README.md").read_text(encoding="utf-8").casefold()
        for text in (description, readme):
            self.assertIn("ordinary", text)
            self.assertIn("independently-major", text)
            self.assertIn("automatic", text)
            self.assertIn("inspect -> schema -> apply", text)
            self.assertNotIn("only an explicit", text)

    def test_plan_option_discovery_regex_normalizes_whitespace(self) -> None:
        source = (ROOT / "skills/teamwork-plan/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Do\nnot compare options or hide it as an assumption.", source)
        validate_skill_source_contract("teamwork-plan", source)

        mutated = source + "\nPlanner may compare options and alternatives.\n"
        with self.assertRaisesRegex(EvalError, "Plan owns option discovery"):
            validate_skill_source_contract("teamwork-plan", mutated)

    def test_default_persistence_cases_cover_writer_routes_and_negative_boundaries(self) -> None:
        cases = {case["id"]: case for case in selected_cases("dev")}
        expected = {
            "persistence-normal-doc-writer",
            "persistence-generic-artifact-writer",
            "persistence-specialized-artifact-writer",
            "persistence-negative-overrides",
            "persistence-explore-no-artifact",
            "persistence-code-coupled-owner",
        }
        self.assertTrue(expected <= set(cases))
        self.assertNotIn("writer", {role for case in load_case_manifest(
            ROOT / "evals/teamwork/live-cases/v4-release-matrix.json"
        ) for role in case["expected_roles"]})

        self.assertEqual(
            {
                "templates/codex-agents/teamwork-writer.toml",
                "templates/cursor-agents/writer.md",
                "templates/claude-agents/writer.md",
            },
            {item["source"] for item in cases["persistence-normal-doc-writer"]["producers"]},
        )
        self.assertIn(
            "scripts/discussion-transaction.py",
            {item["source"] for item in cases["persistence-generic-artifact-writer"]["producers"]},
        )
        self.assertIn(
            "scripts/discussion-transaction.py",
            {item["source"] for item in cases["persistence-specialized-artifact-writer"]["producers"]},
        )
        self.assertIn(
            "skills/teamwork-explore/SKILL.md",
            {item["source"] for item in cases["persistence-explore-no-artifact"]["producers"]},
        )

    def test_generic_persistence_case_requires_working_artifact_transaction_cli(self) -> None:
        case = next(case for case in selected_cases("dev") if case["id"] == "persistence-generic-artifact-writer")
        source_path = "scripts/discussion-transaction.py"
        source = (ROOT / source_path).read_text(encoding="utf-8")
        mutated = source.replace(
            'for name in ("inspect", "design-inspect", "goal-inspect", "artifact-inspect", "artifact-index-validate"):',
            'for name in ("inspect", "design-inspect", "goal-inspect", "artifact-index-validate"):',
            1,
        )
        self.assertNotEqual(source, mutated)
        with self.assertRaisesRegex(EvalError, "artifact-inspect/artifact-schema/artifact-apply"):
            validate_bound_producer_sources(
                case,
                ROOT / "evals/teamwork/cases/persistence-generic-artifact-writer.dev.v4.json",
                {source_path: mutated},
            )

    def test_specialized_persistence_case_requires_working_discussion_transaction_cli(self) -> None:
        case = next(case for case in selected_cases("dev") if case["id"] == "persistence-specialized-artifact-writer")
        source_path = "scripts/discussion-transaction.py"
        source = (ROOT / source_path).read_text(encoding="utf-8")
        mutated = source.replace("def inspect_discussion(", "def removed_inspect_discussion(", 1)
        self.assertNotEqual(source, mutated)
        with self.assertRaisesRegex(EvalError, "inspect/schema/apply"):
            validate_bound_producer_sources(
                case,
                ROOT / "evals/teamwork/cases/persistence-specialized-artifact-writer.dev.v4.json",
                {source_path: mutated},
            )

    def test_each_host_has_exact_nine_role_target_semantics(self) -> None:
        validate_role_template_sources(ROOT)
        for host, mapping in ROLE_TEMPLATE_PATHS.items():
            self.assertEqual(CANONICAL_ROLES, set(mapping))

    def test_bound_producer_rules_cover_every_current_role(self) -> None:
        self.assertEqual(CANONICAL_ROLES, set(case_module.ROLE_SOURCE_RULES))
        self.assertIn(("bounded writing brief",), case_module.ROLE_SOURCE_RULES["writer"])
        self.assertIn(("execution-ready plan packet",), case_module.ROLE_SOURCE_RULES["planner"])

    def test_every_published_v342_case_has_one_active_replacement_disposition(self) -> None:
        mapping = json.loads((ROOT / "evals/teamwork/migrations/v3-case-replacements.json").read_text(encoding="utf-8"))
        listed = [source for group in mapping["groups"] for source in group["sources"]]
        base = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", mapping["base_commit"], "--", "evals/teamwork/cases"],
            text=True, stdout=subprocess.PIPE, check=True,
        ).stdout.splitlines()
        self.assertEqual(sorted(Path(path).name for path in base), sorted(listed))
        self.assertEqual(len(listed), len(set(listed)))
        active = {case["id"] for case in selected_cases("all")}
        for group in mapping["groups"]:
            self.assertTrue(set(group["replacements"]) <= active)

    def test_unsupported_trajectory_never_validates_as_pass(self) -> None:
        record = {
            "schema_version":4,"record_type":"teamwork_host_trajectory_v4","host":"cursor","host_version":"x",
            "invocation_id":"i","arm":"a","started_at":"s","finished_at":"f","case_id":"c","profile":"cost-first",
            "parent_model":"parent","parent_effort":"parent-effort",
            "selected_skill":"UNSUPPORTED","role_identity":"UNSUPPORTED","dispatches":[],
            "actual_model":"UNSUPPORTED","actual_effort":"UNSUPPORTED","tool_observations":[],
            "authority_observation":"UNSUPPORTED","sanitized_input_sha256":"a"*64,
            "artifact":{"path":None,"sha256":None},"result":{"path":None,"sha256":None,"direct_success":False},
            "exit_status":None,"status":"UNSUPPORTED","privacy_scan":"NOT_RUN","failure_classification":"missing-binary",
        }
        validate_trajectory(record)
        record["unexpected"] = True
        with self.assertRaisesRegex(HostMatrixError, "schema forbids"):
            validate_trajectory(record)
        del record["unexpected"]
        record["status"] = "PASS"
        with self.assertRaisesRegex(HostMatrixError, "PASS requires"):
            validate_trajectory(record)

    def test_weakened_candidate_schema_is_rejected_before_record_validation(self) -> None:
        source = ROOT / "evals/teamwork/schemas/host-trajectory-v4.schema.json"
        schema = json.loads(source.read_text(encoding="utf-8"))
        schema["required"] = []
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / source.name
            path.write_text(json.dumps(schema), encoding="utf-8")
            with self.assertRaisesRegex(HostMatrixError, "does not preserve the v4 record contract"):
                load_trajectory_schema(path)

    def test_workspace_pass_requires_a_changed_case_marker_artifact(self) -> None:
        case = next(case for case in load_case_manifest(
            ROOT / "evals/teamwork/live-cases/v4-release-matrix.json"
        ) if case["id"] == "native-result-minimality")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scenario = root / "scenario"
            target = scenario / case["evidence"]["artifact_path"]
            target.parent.mkdir(parents=True)
            target.write_text("PENDING\n", encoding="utf-8")
            unchanged, _artifact, _result, failure = _direct_scenario_evidence(
                case=case, scenario=scenario,
                events=[{"type": "item.completed", "item": {"type": "command_execution"}}],
                output=root / "installed-v4/codex/performance-first.jsonl", invocation_id="unchanged",
                workspace_before=sha256_file(target),
            )
            self.assertFalse(unchanged)
            self.assertEqual("workspace-artifact-unchanged", failure)
            target.write_text("EVIDENCE_NATIVE_RESULT_V4\n", encoding="utf-8")
            changed, artifact, result, failure = _direct_scenario_evidence(
                case=case, scenario=scenario,
                events=[{"type": "item.completed", "item": {"type": "command_execution"}}],
                output=root / "installed-v4/codex/performance-first.jsonl", invocation_id="changed",
                workspace_before=hashlib.sha256(b"PENDING\n").hexdigest(),
            )
            self.assertTrue(changed)
            self.assertIsNone(failure)
            self.assertTrue((root / "installed-v4/codex" / artifact["path"]).is_file())
            self.assertTrue((root / "installed-v4/codex" / result["path"]).is_file())

    def test_agent_self_report_cannot_supply_trace_success_evidence(self) -> None:
        case = next(case for case in load_case_manifest(
            ROOT / "evals/teamwork/live-cases/v4-release-matrix.json"
        ) if case["id"] == "external-research-depth-privacy")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            passed, _artifact, _result, failure = _direct_scenario_evidence(
                case=case, scenario=root,
                events=[{"type": "item.completed", "item": {
                    "type": "agent_message", "text": "EVIDENCE_RESEARCH_DEPTH_V4 direct success",
                }}],
                output=root / "installed-v4/codex/performance-first.jsonl", invocation_id="self-report",
                workspace_before=None,
            )
            self.assertFalse(passed)
            self.assertEqual("trace-markers-missing", failure)

    def test_workspace_verifier_refuses_a_modified_candidate_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = Path(temporary)
            verifier = scenario / "scenario/verify.py"
            verifier.parent.mkdir(parents=True)
            verifier.write_text("raise SystemExit(0)\n", encoding="utf-8")
            spec = {"verification": {"argv": ["python3", "scenario/verify.py"], "immutable_paths": ["scenario/verify.py"]}}
            before = _immutable_scenario_hashes(scenario, spec)
            verifier.write_text("raise SystemExit(1)\n", encoding="utf-8")
            passed, failure = _run_scenario_verifier(scenario, spec, before, 10)
            self.assertFalse(passed)
            self.assertEqual("scenario-verifier-modified", failure)

    def test_matrix_verifier_requires_thirteen_and_all_roles_in_each_slice(self) -> None:
        cases = load_case_manifest(
            ROOT / "evals/teamwork/manifests/v4.1.0-teamwork-c5-cases.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "evals/teamwork/outputs/installed-v4"
            spec = importlib.util.spec_from_file_location(
                "teamwork_release_matrix_test",
                SCRIPTS / "run-teamwork-release-matrix.py",
            )
            assert spec and spec.loader
            release_matrix = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(release_matrix)
            slices = [
                ("codex", "performance-first", "performance-first-root-gpt55-low"),
                ("codex", "performance-first", "performance-first-root-gpt55-high"),
                ("codex", "cost-first", "cost-first-root-gpt55-low"),
                ("codex", "cost-first", "cost-first-root-gpt55-high"),
                ("cursor", "performance-first", "performance-first"),
                ("cursor", "cost-first", "cost-first"),
                ("claude", "performance-first", "performance-first"),
                ("claude", "cost-first", "cost-first"),
            ]
            for host, profile, arm in slices:
                path = output_root / host / f"{arm}.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                records = []
                for index, case in enumerate(cases):
                    roles = case["expected_roles"]
                    evidence_dir = path.parent / "artifacts" / f"{host}-{arm}-{index}"
                    evidence_dir.mkdir(parents=True, exist_ok=True)
                    artifact_path = evidence_dir / "trace.jsonl"
                    result_path = evidence_dir / "result.txt"
                    artifact_path.write_text("actual host tool trace\n", encoding="utf-8")
                    result_path.write_text(
                        "\n".join(case["evidence"]["markers"]) + "\n", encoding="utf-8"
                    )
                    expected = case["role_expectations"][host][profile][case["required_role"]]
                    invocation_id = f"{host}-{arm}-{index}"
                    dispatches = [
                        dispatch_for(
                            host,
                            role,
                            invocation_id,
                            case["role_expectations"][host][profile][role]["model"],
                            case["role_expectations"][host][profile][role]["effort"],
                        )
                        for role in roles
                    ]
                    record = {
                        "schema_version":4,"record_type":"teamwork_host_trajectory_v4","host":host,"host_version":"test",
                        "invocation_id":invocation_id,"arm":arm,"started_at":"s","finished_at":"f","case_id":case["id"],"profile":profile,
                        "parent_model":"parent-model","parent_effort":"parent-effort",
                        "selected_skill":case["selected_skill"],"role_identity":case["required_role"],"dispatches":dispatches,
                        "actual_model":expected["model"],"actual_effort":expected["effort"],"tool_observations":case["required_tools"],
                        "authority_observation":case["authority"],"sanitized_input_sha256":hashlib.sha256(case["prompt"].encode()).hexdigest(),
                        "artifact":{"path":artifact_path.relative_to(path.parent).as_posix(),"sha256":hashlib.sha256(artifact_path.read_bytes()).hexdigest()},
                        "result":{"path":result_path.relative_to(path.parent).as_posix(),"sha256":hashlib.sha256(result_path.read_bytes()).hexdigest(),"direct_success":True},
                        "exit_status":0,"status":"PASS","privacy_scan":"PASS","failure_classification":None,
                    }
                    records.append(record)
                path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
            command = [
                sys.executable, str(SCRIPTS / "run-teamwork-release-matrix.py"), "verify",
                "--manifest", str(ROOT / "evals/teamwork/manifests/v4.1.0-teamwork-c5-cases.json"),
                "--output-root", str(output_root),
                "--schema", str(ROOT / "evals/teamwork/schemas/host-trajectory-v4.schema.json"),
                "--hosts", "codex", "cursor", "claude",
                "--profiles", "performance-first", "cost-first",
                "--codex-arms",
                "performance-first-root-gpt55-low",
                "performance-first-root-gpt55-high",
                "cost-first-root-gpt55-low",
                "cost-first-root-gpt55-high",
                "--expected-records-per-output", "13",
                "--expected-total-records", "104",
                "--required-roles-per-slice", *sorted(LEGACY_V4_C5_ROLES),
                "--summary", str(output_root / "matrix-summary.json"),
            ]

            def run_verify() -> subprocess.CompletedProcess[str]:
                Path(command[-1]).unlink(missing_ok=True)
                stdout = io.StringIO()
                stderr = io.StringIO()
                with (
                    mock.patch.object(sys, "argv", command[1:]),
                    mock.patch.object(sys, "stdout", stdout),
                    mock.patch.object(sys, "stderr", stderr),
                    mock.patch.object(
                        release_matrix,
                        "C5_TEMP_ROOT",
                        output_root.parents[1],
                    ),
                ):
                    returncode = release_matrix.main()
                return subprocess.CompletedProcess(
                    command,
                    returncode,
                    stdout.getvalue(),
                    stderr.getvalue(),
                )

            passed = run_verify()
            self.assertEqual(0, passed.returncode, passed.stderr)
            generic_path = output_root / "codex/performance-first-root-gpt55-low.jsonl"
            generic = [json.loads(line) for line in generic_path.read_text(encoding="utf-8").splitlines()]
            generic[0]["actual_model"] = "observed-model"
            generic_path.write_text("".join(json.dumps(record) + "\n" for record in generic), encoding="utf-8")
            generic_failed = run_verify()
            self.assertEqual(1, generic_failed.returncode)
            self.assertIn("non-generic actual_model", generic_failed.stderr)
            expected_codex_performance = cases[0]["role_expectations"]["codex"]["performance-first"][cases[0]["required_role"]]
            generic[0]["actual_model"] = expected_codex_performance["model"]
            generic[0]["actual_effort"] = expected_codex_performance["effort"]
            generic_path.write_text("".join(json.dumps(record) + "\n" for record in generic), encoding="utf-8")

            # Make each record otherwise bind to a real, alternate host/profile.
            # It must still be refused because this is the codex/performance slice.
            expected_cursor_performance = cases[0]["role_expectations"]["cursor"]["performance-first"][cases[0]["required_role"]]
            generic[0]["host"] = "cursor"
            generic[0]["actual_model"] = expected_cursor_performance["model"]
            generic[0]["actual_effort"] = expected_cursor_performance["effort"]
            generic_path.write_text("".join(json.dumps(record) + "\n" for record in generic), encoding="utf-8")
            cross_host = run_verify()
            self.assertEqual(1, cross_host.returncode)
            self.assertIn("record host/profile does not match containing output slice codex/performance-first", cross_host.stderr)

            expected_codex_cost = cases[0]["role_expectations"]["codex"]["cost-first"][cases[0]["required_role"]]
            generic[0]["host"] = "codex"
            generic[0]["profile"] = "cost-first"
            generic[0]["actual_model"] = expected_codex_cost["model"]
            generic[0]["actual_effort"] = expected_codex_cost["effort"]
            generic_path.write_text("".join(json.dumps(record) + "\n" for record in generic), encoding="utf-8")
            cross_profile = run_verify()
            self.assertEqual(1, cross_profile.returncode)
            self.assertIn("record host/profile does not match containing output slice codex/performance-first", cross_profile.stderr)

            generic[0]["profile"] = "performance-first"
            generic[0]["actual_model"] = expected_codex_performance["model"]
            generic[0]["actual_effort"] = expected_codex_performance["effort"]
            generic_path.write_text("".join(json.dumps(record) + "\n" for record in generic), encoding="utf-8")
            blocked_path = output_root / "cursor/cost-first.jsonl"
            blocked = [json.loads(line) for line in blocked_path.read_text(encoding="utf-8").splitlines()]
            multi_role_index = next(
                index for index, record in enumerate(blocked)
                if len(record["dispatches"]) > 1
            )
            blocked[multi_role_index]["dispatches"] = blocked[multi_role_index]["dispatches"][:-1]
            blocked_path.write_text("".join(json.dumps(record) + "\n" for record in blocked), encoding="utf-8")
            failed = run_verify()
            self.assertEqual(1, failed.returncode)
            self.assertIn("role identity/coverage", failed.stderr)


if __name__ == "__main__":
    unittest.main()
