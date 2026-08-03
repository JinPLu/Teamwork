from __future__ import annotations

import json
import hashlib
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_case_transaction_contract")


class CaseArtifactTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        self.write_index(CONTRACT["empty_case_index"]("Teamwork"))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_index(self, index: dict[str, object]) -> None:
        (self.memory / "index.json").write_text(CONTRACT["serialize_case_index"](index), encoding="utf-8")

    def cli(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, text=True, capture_output=True, env=merged, check=False)

    def inspect(self) -> dict[str, object]:
        result = self.cli("case-inspect", "--project-root", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def schema(self, operation: str) -> dict[str, object]:
        result = self.cli("case-schema", operation)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def apply(self, request: dict[str, object], *, env: dict[str, str] | None = None) -> dict[str, object]:
        result = self.cli("case-apply", "--project-root", str(self.project), "--request-json", json.dumps(request), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def base_request(self, operation: str, case: dict[str, object] | None = None, **extra: object) -> dict[str, object]:
        request: dict[str, object] = {
            "schema_version": 2,
            "operation": operation,
            "expected_revision": self.inspect()["revision"],
            "updated_at": "2026-07-30T00:00:00+00:00",
        }
        if case is not None:
            request["case_id"] = case["case_id"]
            request["expected_manifest_revision"] = case["manifest_revision"]
        request.update(extra)
        return request

    def schema_request(self, operation: str, case: dict[str, object] | None = None, **extra: object) -> dict[str, object]:
        request = self.schema(operation)
        request["expected_revision"] = self.inspect()["revision"]
        request["updated_at"] = extra.pop("updated_at", "2026-07-30T00:00:00+00:00")
        if case is not None:
            request["case_id"] = case["case_id"]
            request["expected_manifest_revision"] = case["manifest_revision"]
        request.update(extra)
        return request

    def create_case(self, seed: str = "01" * 32, task_key: str = "persistent-docs", initial_phase: str = "collaborating") -> dict[str, object]:
        return self.apply(
            self.base_request(
                "create",
                case_seed=seed,
                title=f"Case {task_key}",
                task_key=task_key,
                aliases=[task_key],
                initial_phase=initial_phase,
            )
        )

    def active_case(self, case_id: str) -> dict[str, object]:
        inspected = self.inspect()
        return next(item for item in inspected["active_cases"] if item["state"]["case_id"] == case_id)

    def assert_artifact_records_match_extant_bytes(self, case_id: str) -> dict[str, object]:
        manifest = json.loads((self.project / f"docs/teamwork/cases/{case_id}/manifest.json").read_text(encoding="utf-8"))
        paths: list[str] = []
        for artifact_id, row in manifest["artifacts"].items():
            path = self.project / row["path"]
            self.assertTrue(path.is_file(), f"{artifact_id} path missing: {row['path']}")
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["byte_digest"], artifact_id)
            paths.append(row["path"])
        self.assertEqual(len(paths), len(set(paths)))
        return manifest

    def test_schema_driven_writer_matrix_binds_operation_kind_consumer_lifecycle_and_readback(self) -> None:
        contracts = (
            ("collaborate-upsert", "collaborating", "collaborating", "collaborate", "collaborate", {}),
            ("accept-decision", "collaborating", "collaborating", "decision", "decision", {}),
            ("evidence-add", "collecting", "collecting", "evidence", "evidence", {}),
            ("research-add", "collecting", "collecting", "research", "evidence", {}),
            ("debug-add", "collecting", "collecting", "debug", "evidence", {}),
            ("init-result", "collecting", "collecting", "init", "evidence", {}),
            ("update-result", "collecting", "collecting", "update", "evidence", {}),
            ("native-result", "executing", "executing", "result", "result", {}),
            ("plan-upsert", "planned", "executing", "plan", "plan", {}),
            ("plan-review-add", "planned", "planned", "review", "review", {"sealed_candidate_digest": "91" * 32}),
            ("review-add", "executing", "reviewing", "review", "review", {"sealed_candidate_digest": "92" * 32}),
            ("code-review-add", "executing", "reviewing", "review", "review", {"sealed_candidate_digest": "93" * 32}),
            ("result-add", "executing", "executing", "result", "result", {}),
            ("goal-acquire", "executing", "executing", "goal", "goal", {"claim_seed": "94" * 32, "owner": "Goal"}),
            ("goal-update", "executing", "executing", "goal", "goal", {"claim_seed": "95" * 32, "owner": "Goal"}),
        )
        for index, (operation, phase, final_phase, kind, role, extra) in enumerate(contracts, start=1):
            with self.subTest(operation=operation):
                created = self.apply(
                    self.schema_request(
                        "create",
                        case_seed=f"{index:064x}",
                        title=f"Writer route {operation}",
                        task_key=f"writer-route-{operation}",
                        aliases=[],
                        initial_phase=phase,
                    )
                )
                request = self.schema_request(
                    operation,
                    created,
                    source_digest=f"{index + 32:064x}",
                    body=f"## {operation}\n\n- Schema-derived persistence route.",
                    **extra,
                )
                self.assertEqual(request["kind"], kind)
                self.assertEqual(request["consumer"], "teamwork")
                applied = self.apply(request)
                readback = self.active_case(str(applied["case_id"]))
                manifest = readback["state"]
                self.assertEqual(readback["revision"], applied["manifest_revision"])
                self.assertEqual(manifest["status"], final_phase)
                self.assertEqual(len(manifest["artifacts"]), 1)
                artifact = next(iter(manifest["artifacts"].values()))
                self.assertEqual(artifact["role"], role)
                self.assertEqual(artifact["subtype"], kind)
                self.assertEqual(artifact["consumer"], "teamwork")
                self.assertTrue((self.project / artifact["path"]).is_file())

    def test_schema_driven_writer_routes_reject_cross_kind_and_consumer_overrides(self) -> None:
        created = self.apply(
            self.schema_request(
                "create",
                case_seed="a1" * 32,
                title="Writer route override rejection",
                task_key="writer-route-override-rejection",
                aliases=[],
                initial_phase="collecting",
            )
        )
        invalid = (
            ("kind", "research", "evidence-add kind must be evidence"),
            ("consumer", "external", "evidence-add consumer must be teamwork"),
        )
        for field, value, message in invalid:
            with self.subTest(field=field):
                request = self.schema_request(
                    "evidence-add",
                    created,
                    source_digest="a2" * 32,
                    body="## Evidence\n\n- Reject semantic drift.",
                )
                request[field] = value
                result = self.cli(
                    "case-apply",
                    "--project-root",
                    str(self.project),
                    "--request-json",
                    json.dumps(request),
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, json.loads(result.stderr)["message"])
                self.assertEqual(self.active_case(str(created["case_id"]))["state"]["artifacts"], {})

    def test_case_create_plan_and_close_are_journaled_under_v2_paths(self) -> None:
        created = self.create_case(initial_phase="planned")
        case_id = created["case_id"]
        manifest_path = self.project / created["manifest_path"]
        self.assertTrue(manifest_path.is_file())
        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8"))["status"], "planned")

        planned = self.apply(
            self.base_request(
                "plan-upsert",
                created,
                source_digest="1" * 64,
                body="## Plan\n\n- Implement case bundle.",
            )
        )
        plan_path = self.project / f"docs/teamwork/cases/{case_id}/plan.md"
        self.assertTrue(plan_path.is_file())
        self.assertIn("Artifact Type: case-plan", plan_path.read_text(encoding="utf-8"))
        manifest = json.loads((self.project / planned["manifest_path"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "executing")
        self.assertEqual(next(iter(manifest["artifacts"].values()))["path"], f"docs/teamwork/cases/{case_id}/plan.md")

        executing = self.apply(
            self.base_request(
                "result-add",
                planned,
                updated_at="2026-07-30T01:30:00+00:00",
                source_digest="3" * 64,
                body="## Result\n\n- Terminal result.",
            )
        )
        closed = self.apply(
            self.base_request(
                "close",
                executing,
                updated_at="2026-07-30T02:00:00+00:00",
                closed_at="2026-07-30T02:00:00+00:00",
            )
        )
        self.assertEqual(closed["changed_paths"], sorted(closed["changed_paths"]))
        inspected = self.inspect()
        self.assertEqual(inspected["active_cases"], [])
        self.assertEqual(inspected["recent_cases"][0]["case_id"], case_id)
        self.assertRegex(inspected["recent_cases"][0]["result_artifact_id"], r"^a-[0-9a-f]{64}$")

    def test_recent_case_rollover_prunes_aliases_to_hot_cases(self) -> None:
        closed_case_ids: list[str] = []
        for index in range(11):
            created = self.create_case(
                seed=f"{index + 1:064x}",
                task_key=f"rollover-{index}",
                initial_phase="executing",
            )
            completed = self.apply(
                self.base_request(
                    "result-add",
                    created,
                    updated_at=f"2026-07-30T{index:02d}:15:00+00:00",
                    source_digest=f"{index + 101:064x}",
                    body=f"## Result\n\n- Closed case {index}.",
                )
            )
            self.apply(
                self.base_request(
                    "close",
                    completed,
                    updated_at=f"2026-07-30T{index:02d}:30:00+00:00",
                    closed_at=f"2026-07-30T{index:02d}:30:00+00:00",
                )
            )
            closed_case_ids.append(str(created["case_id"]))

        inspected = self.inspect()
        hot_case_ids = {row["case_id"] for row in inspected["recent_cases"]}
        self.assertEqual(len(hot_case_ids), 10)
        self.assertEqual(hot_case_ids, set(closed_case_ids[-10:]))
        self.assertEqual(
            {row["target_id"] for row in inspected["aliases"].values()},
            hot_case_ids,
        )
        CONTRACT["validate_case_v2_tree_readonly"](self.project)

    def test_create_reuses_stale_alias_from_pre_pruning_index(self) -> None:
        prior = self.create_case(
            seed="71" * 32,
            task_key="reusable-stale-alias",
            initial_phase="executing",
        )
        completed = self.apply(
            self.base_request(
                "result-add",
                prior,
                source_digest="72" * 32,
                body="## Result\n\n- Pre-upgrade closed case.",
            )
        )
        self.apply(
            self.base_request(
                "close",
                completed,
                updated_at="2026-07-30T02:00:00+00:00",
                closed_at="2026-07-30T02:00:00+00:00",
            )
        )

        stale_index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        stale_index["recent_cases"] = []
        self.assertEqual(
            stale_index["aliases"]["reusable-stale-alias"]["target_id"],
            prior["case_id"],
        )
        self.write_index(stale_index)

        replacement = self.create_case(
            seed="73" * 32,
            task_key="reusable-stale-alias",
            initial_phase="collecting",
        )
        inspected = self.inspect()
        self.assertEqual(
            inspected["aliases"]["reusable-stale-alias"]["target_id"],
            replacement["case_id"],
        )
        self.assertNotEqual(replacement["case_id"], prior["case_id"])
        CONTRACT["validate_case_v2_tree_readonly"](self.project)

    def test_legacy_v1_index_is_migration_input_only_for_runtime(self) -> None:
        v1 = {
            "schema_version": 1,
            "last_updated": "2026-07-30",
            "project": {"name": "Teamwork", "root": ".", "description": "legacy"},
            "active": {"current": "docs/teamwork/current.md", "design": None, "plan": None, "progress": None, "report": None, "results": [], "collaborate": None},
            "entries": [{"topic": "legacy", "kind": "report", "title": "Legacy", "status": "historical", "currentness": "historical", "authority": "historical", "path": "docs/teamwork/current.md", "updated": "2026-07-30", "summary": "Legacy"}],
        }
        (self.memory / "index.json").write_text(json.dumps(v1, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.memory / "current.md").write_text("# Current\n", encoding="utf-8")
        before_index = (self.memory / "index.json").read_bytes()
        inspected = self.cli("case-inspect", "--project-root", str(self.project))
        self.assertNotEqual(inspected.returncode, 0)
        self.assertEqual(json.loads(inspected.stderr)["category"], "PREWRITE_SAFE")
        preflight = self.cli("migration-preflight", "--project-root", str(self.project))
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        self.assertEqual(json.loads(preflight.stdout)["mode"], "legacy-v1")
        result = self.cli(
            "case-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps({
                "schema_version": 2,
                "operation": "create",
                "expected_revision": "stale",
                "updated_at": "2026-07-30T00:00:00+00:00",
                "case_seed": "03" * 32,
                "title": "Blocked",
                "task_key": "blocked",
                "aliases": [],
            }),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual((self.memory / "index.json").read_bytes(), before_index)

    def test_runtime_collaborate_state_rejects_retired_grill_mode(self) -> None:
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "Collaborate mode is invalid"):
            CONTRACT["normalize_collaborate_state"](
                {
                    "decision_id": "c-retired-grill",
                    "slug": "retired-grill",
                    "title": "Retired Grill",
                    "updated": "2026-07-30T00:00:00Z",
                    "status": "active",
                    "acceptance": "pending",
                    "mode": "grill",
                    "goal": "Reject retired runtime mode.",
                    "frontier": [{"id": "Q1", "title": "Boundary", "rationale": "Legacy grill routing.", "status": "open"}],
                    "current_batch": ["Q1"],
                }
            )

    def test_goal_claim_transfer_binds_source_target_and_root_head(self) -> None:
        source = self.create_case("11" * 32, "source-case")
        target = self.create_case("22" * 32, "target-case")
        source = self.apply(self.base_request("update", source, phase="planned", updated_at="2026-07-30T00:30:00+00:00"))
        source = self.apply(self.base_request("update", source, phase="executing", updated_at="2026-07-30T01:00:00+00:00"))
        acquired = self.apply(
            self.base_request(
                "goal-acquire",
                source,
                updated_at="2026-07-30T01:30:00+00:00",
                source_digest="2" * 64,
                body="## Goal\n\n- Keep working.",
                claim_seed="33" * 32,
                owner="Goal",
            )
        )
        source_manifest = json.loads((self.project / acquired["manifest_path"]).read_text(encoding="utf-8"))
        claim_id, claim = next(iter(source_manifest["claims"].items()))
        artifact_id = claim["head_artifact_id"]
        target_state = self.active_case(target["case_id"])
        transferred = self.apply(
            self.base_request(
                "goal-transfer",
                acquired,
                updated_at="2026-07-30T02:00:00+00:00",
                artifact_id=artifact_id,
                new_case_id=target["case_id"],
                new_expected_manifest_revision=target_state["revision"],
            )
        )
        inspected = self.inspect()
        self.assertEqual(inspected["claim_heads"][claim_id]["case_id"], target["case_id"])
        source_manifest = json.loads((self.project / transferred["manifest_path"]).read_text(encoding="utf-8"))
        target_manifest = json.loads((self.project / f"docs/teamwork/cases/{target['case_id']}/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(source_manifest["claims"][claim_id]["status"], "released")
        self.assertEqual(target_manifest["claims"][claim_id]["status"], "active")

    def test_goal_live_updates_relocate_prior_immutable_records_to_matching_history_bytes(self) -> None:
        created = self.create_case("33" * 32, "goal-live", initial_phase="planned")
        executing = self.apply(self.base_request("update", created, phase="executing", updated_at="2026-07-30T00:30:00+00:00"))
        acquired = self.apply(
            self.base_request(
                "goal-acquire",
                executing,
                updated_at="2026-07-30T01:00:00+00:00",
                source_digest="1" * 64,
                body="## Goal\n\n- First live goal.",
                claim_seed="34" * 32,
                owner="Goal",
            )
        )
        first_live = (self.project / f"docs/teamwork/cases/{acquired['case_id']}/live/goal.md").read_bytes()
        updated_once = self.apply(
            self.base_request(
                "goal-update",
                acquired,
                updated_at="2026-07-30T01:10:00+00:00",
                source_digest="2" * 64,
                body="## Goal\n\n- Second live goal.",
                claim_seed="34" * 32,
                owner="Goal",
            )
        )
        updated_twice = self.apply(
            self.base_request(
                "goal-update",
                updated_once,
                updated_at="2026-07-30T01:20:00+00:00",
                source_digest="3" * 64,
                body="## Goal\n\n- Third live goal.",
                claim_seed="34" * 32,
                owner="Goal",
            )
        )
        manifest = self.assert_artifact_records_match_extant_bytes(str(updated_twice["case_id"]))
        live_path = f"docs/teamwork/cases/{updated_twice['case_id']}/live/goal.md"
        self.assertEqual(manifest["runtime"]["active_route"], live_path)
        live_records = [row for row in manifest["artifacts"].values() if row["path"] == live_path]
        self.assertEqual(len(live_records), 1)
        archived_records = [row for row in manifest["artifacts"].values() if row["path"].startswith(f"docs/teamwork/cases/{updated_twice['case_id']}/history/live/")]
        self.assertEqual(len(archived_records), 2)
        self.assertIn(first_live, [(self.project / row["path"]).read_bytes() for row in archived_records])

    def test_collaborate_live_upserts_relocate_prior_immutable_records_and_accept_decision_stays_separate(self) -> None:
        created = self.create_case("36" * 32, "collaborate-live", initial_phase="collaborating")
        first = self.apply(
            self.base_request(
                "collaborate-upsert",
                created,
                updated_at="2026-07-30T01:00:00+00:00",
                source_digest="4" * 64,
                body="## Collaborate\n\n- First checkpoint.",
            )
        )
        second = self.apply(
            self.base_request(
                "collaborate-upsert",
                first,
                updated_at="2026-07-30T01:10:00+00:00",
                source_digest="5" * 64,
                body="## Collaborate\n\n- Second checkpoint.",
            )
        )
        third = self.apply(
            self.base_request(
                "collaborate-upsert",
                second,
                updated_at="2026-07-30T01:20:00+00:00",
                source_digest="6" * 64,
                body="## Collaborate\n\n- Third checkpoint.",
            )
        )
        accepted = self.apply(
            self.base_request(
                "accept-decision",
                third,
                updated_at="2026-07-30T01:30:00+00:00",
                source_digest="7" * 64,
                body="## Decision\n\n- Accepted decision.",
            )
        )
        manifest = self.assert_artifact_records_match_extant_bytes(str(accepted["case_id"]))
        collaborate_live = f"docs/teamwork/cases/{accepted['case_id']}/live/collaborate.md"
        self.assertTrue((self.project / collaborate_live).is_file())
        self.assertTrue((self.project / f"docs/teamwork/cases/{accepted['case_id']}/decision.md").is_file())
        self.assertEqual(manifest["runtime"]["active_route"], f"docs/teamwork/cases/{accepted['case_id']}/decision.md")
        self.assertEqual(len([row for row in manifest["artifacts"].values() if row["path"] == collaborate_live]), 1)
        self.assertEqual(len([row for row in manifest["artifacts"].values() if row["role"] == "collaborate"]), 3)
        self.assertEqual(len([row for row in manifest["artifacts"].values() if row["path"].startswith(f"docs/teamwork/cases/{accepted['case_id']}/history/live/")]), 2)

    def test_decision_revisions_relocate_prior_singleton_record_to_matching_history_bytes(self) -> None:
        created = self.create_case("37" * 32, "decision-revision", initial_phase="collaborating")
        first = self.apply(
            self.base_request(
                "accept-decision",
                created,
                updated_at="2026-07-30T01:00:00+00:00",
                source_digest="8" * 64,
                body="## Decision\n\n- First decision.",
            )
        )
        second = self.apply(
            self.base_request(
                "accept-decision",
                first,
                updated_at="2026-07-30T01:10:00+00:00",
                source_digest="9" * 64,
                body="## Decision\n\n- Revised decision.",
            )
        )
        manifest = self.assert_artifact_records_match_extant_bytes(str(second["case_id"]))
        decision_path = f"docs/teamwork/cases/{second['case_id']}/decision.md"
        self.assertEqual(manifest["runtime"]["active_route"], decision_path)
        self.assertEqual(len([row for row in manifest["artifacts"].values() if row["path"] == decision_path]), 1)
        self.assertEqual(len([row for row in manifest["artifacts"].values() if row["path"].startswith(f"docs/teamwork/cases/{second['case_id']}/history/decision/")]), 1)

    def test_planned_case_can_receive_an_imported_accepted_decision(self) -> None:
        created = self.create_case("39" * 32, "planned-decision-repair", initial_phase="planned")
        accepted = self.apply(
            self.base_request(
                "accept-decision",
                created,
                updated_at="2026-07-30T01:00:00+00:00",
                source_digest="b" * 64,
                body="## Decision\n\n- Accepted before the imported plan.",
            )
        )
        manifest = self.assert_artifact_records_match_extant_bytes(str(accepted["case_id"]))
        self.assertEqual(manifest["status"], "planned")
        self.assertEqual(
            manifest["runtime"]["active_route"],
            f"docs/teamwork/cases/{accepted['case_id']}/decision.md",
        )

    def test_plan_revisions_relocate_prior_singleton_record_to_matching_history_bytes(self) -> None:
        created = self.create_case("38" * 32, "plan-revision", initial_phase="planned")
        first = self.apply(
            self.base_request(
                "plan-upsert",
                created,
                updated_at="2026-07-30T01:00:00+00:00",
                source_digest="a" * 64,
                body="## Plan\n\n- First plan.",
            )
        )
        self.assertEqual(json.loads((self.project / first["manifest_path"]).read_text(encoding="utf-8"))["status"], "executing")
        second = self.apply(
            self.base_request(
                "plan-upsert",
                first,
                updated_at="2026-07-30T01:10:00+00:00",
                source_digest="b" * 64,
                body="## Plan\n\n- Revised plan.",
            )
        )
        manifest = self.assert_artifact_records_match_extant_bytes(str(second["case_id"]))
        plan_path = f"docs/teamwork/cases/{second['case_id']}/plan.md"
        self.assertEqual(manifest["runtime"]["active_route"], plan_path)
        self.assertEqual(len([row for row in manifest["artifacts"].values() if row["path"] == plan_path]), 1)
        self.assertEqual(len([row for row in manifest["artifacts"].values() if row["path"].startswith(f"docs/teamwork/cases/{second['case_id']}/history/plan/")]), 1)

    def test_singleton_history_collision_and_stale_replay_do_not_overwrite_live_bytes(self) -> None:
        created = self.create_case("39" * 32, "singleton-collision", initial_phase="collaborating")
        first_request = self.base_request(
            "accept-decision",
            created,
            updated_at="2026-07-30T01:00:00+00:00",
            source_digest="c" * 64,
            body="## Decision\n\n- First decision.",
        )
        first = self.apply(first_request)
        decision_path = self.project / f"docs/teamwork/cases/{first['case_id']}/decision.md"
        live_before = decision_path.read_bytes()

        stale = self.cli("case-apply", "--project-root", str(self.project), "--request-json", json.dumps(first_request))
        self.assertNotEqual(stale.returncode, 0)
        self.assertEqual(decision_path.read_bytes(), live_before)

        manifest = json.loads((self.project / first["manifest_path"]).read_text(encoding="utf-8"))
        prior_id = next(artifact_id for artifact_id, row in manifest["artifacts"].items() if row["path"].endswith("/decision.md"))
        collision = self.project / f"docs/teamwork/cases/{first['case_id']}/history/decision/{prior_id}.md"
        collision.parent.mkdir(parents=True)
        collision.write_text("collision\n", encoding="utf-8")
        second_request = self.base_request(
            "accept-decision",
            first,
            updated_at="2026-07-30T01:10:00+00:00",
            source_digest="d" * 64,
            body="## Decision\n\n- Revised decision.",
        )
        blocked = self.cli("case-apply", "--project-root", str(self.project), "--request-json", json.dumps(second_request))
        self.assertNotEqual(blocked.returncode, 0)
        self.assertEqual(json.loads(blocked.stderr)["category"], "INDETERMINATE")
        self.assertEqual(decision_path.read_bytes(), live_before)
        self.assertEqual(collision.read_text(encoding="utf-8"), "collision\n")

    def test_sealed_candidate_review_and_delta_are_not_overwritten(self) -> None:
        created = self.create_case("44" * 32, "review-delta", initial_phase="planned")
        executing = self.apply(self.base_request("update", created, phase="executing", updated_at="2026-07-30T00:30:00+00:00"))
        review_request = self.base_request(
            "code-review-add",
            executing,
            updated_at="2026-07-30T01:00:00+00:00",
            source_digest="4" * 64,
            sealed_candidate_digest="5" * 64,
            body="## Review\n\n- Accept base.",
        )
        reviewed = self.apply(review_request)
        review_path = self.project / f"docs/teamwork/cases/{reviewed['case_id']}/reviews/{'5' * 64}.md"
        original = review_path.read_bytes()

        duplicate = self.cli("case-apply", "--project-root", str(self.project), "--request-json", json.dumps({
            **review_request,
            "expected_revision": self.inspect()["revision"],
            "expected_manifest_revision": reviewed["manifest_revision"],
            "updated_at": "2026-07-30T01:10:00+00:00",
            "body": "## Review\n\n- Attempt overwrite.",
        }))
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertEqual(review_path.read_bytes(), original)

        delta = self.apply(self.base_request(
            "code-review-add",
            reviewed,
            updated_at="2026-07-30T01:20:00+00:00",
            source_digest="6" * 64,
            sealed_candidate_digest="5" * 64,
            delta=True,
            body="## Review\n\n- Delta recheck.",
        ))
        delta_path = self.project / f"docs/teamwork/cases/{reviewed['case_id']}/reviews/{'5' * 64}-delta.md"
        delta_original = delta_path.read_bytes()
        duplicate_delta = self.cli("case-apply", "--project-root", str(self.project), "--request-json", json.dumps({
            "schema_version": 2,
            "operation": "code-review-add",
            "expected_revision": self.inspect()["revision"],
            "case_id": delta["case_id"],
            "expected_manifest_revision": delta["manifest_revision"],
            "updated_at": "2026-07-30T01:30:00+00:00",
            "source_digest": "7" * 64,
            "sealed_candidate_digest": "5" * 64,
            "delta": True,
            "body": "## Review\n\n- Attempt delta overwrite.",
        }))
        self.assertNotEqual(duplicate_delta.returncode, 0)
        self.assertEqual(delta_path.read_bytes(), delta_original)

    def test_review_delta_uses_separate_immutable_slot_without_base_review(self) -> None:
        created = self.create_case("45" * 32, "separate-delta", initial_phase="planned")
        executing = self.apply(self.base_request("update", created, phase="executing", updated_at="2026-07-30T00:30:00+00:00"))
        delta = self.apply(
            self.base_request(
                "code-review-add",
                executing,
                updated_at="2026-07-30T01:00:00+00:00",
                source_digest="8" * 64,
                sealed_candidate_digest="9" * 64,
                delta=True,
                body="## Review\n\n- Delta for repaired candidate.",
            )
        )
        delta_path = self.project / f"docs/teamwork/cases/{delta['case_id']}/reviews/{'9' * 64}-delta.md"
        self.assertTrue(delta_path.is_file())
        base_path = self.project / f"docs/teamwork/cases/{delta['case_id']}/reviews/{'9' * 64}.md"
        self.assertFalse(base_path.exists())

    def test_operation_phase_matrix_is_not_silently_widened(self) -> None:
        cases = [
            ("research-add", "collaborating", False),
            ("research-add", "collecting", True),
            ("research-add", "planned", True),
            ("research-add", "executing", True),
            ("research-add", "reviewing", True),
            ("debug-add", "collaborating", False),
            ("debug-add", "collecting", True),
            ("collaborate-upsert", "collaborating", True),
            ("collaborate-upsert", "reviewing", True),
            ("init-result", "planned", False),
            ("init-result", "collecting", True),
            ("init-result", "executing", True),
            ("update-result", "planned", False),
            ("native-result", "reviewing", False),
            ("native-result", "collecting", True),
            ("plan-upsert", "collaborating", False),
            ("plan-upsert", "collecting", False),
            ("plan-upsert", "planned", True),
            ("plan-upsert", "executing", True),
            ("plan-review-add", "planned", True),
            ("plan-review-add", "executing", False),
            ("code-review-add", "executing", True),
        ]
        for position, (operation, phase, allowed) in enumerate(cases):
            with self.subTest(operation=operation, phase=phase):
                project = Path(self.temporary.name) / f"matrix-{position}"
                memory = project / "docs/teamwork"
                memory.mkdir(parents=True)
                (memory / "index.json").write_text(CONTRACT["serialize_case_index"](CONTRACT["empty_case_index"]("Teamwork")), encoding="utf-8")
                old_project, old_memory = self.project, self.memory
                self.project, self.memory = project, memory
                try:
                    created = self.create_case(f"{position + 1:064x}", f"matrix-{position}", initial_phase=phase if phase in {"collaborating", "collecting", "planned"} else "planned")
                    if phase == "executing":
                        created = self.apply(self.base_request("update", created, phase="executing", updated_at="2026-07-30T00:30:00+00:00"))
                    elif phase == "reviewing":
                        created = self.apply(self.base_request("update", created, phase="executing", updated_at="2026-07-30T00:30:00+00:00"))
                        created = self.apply(
                            self.base_request(
                                "code-review-add",
                                created,
                                updated_at="2026-07-30T00:45:00+00:00",
                                source_digest="9" * 64,
                                sealed_candidate_digest=f"{position + 200:064x}",
                                body="## Review\n\n- Seal.",
                            )
                        )
                    request = self.base_request(
                        operation,
                        created,
                        updated_at="2026-07-30T01:00:00+00:00",
                        source_digest="8" * 64,
                        body="## Body\n\n- Evidence.",
                    )
                    if operation in {"review-add", "code-review-add", "plan-review-add"}:
                        request["sealed_candidate_digest"] = f"{position + 100:064x}"
                    result = self.cli("case-apply", "--project-root", str(self.project), "--request-json", json.dumps(request))
                    if allowed:
                        self.assertEqual(result.returncode, 0, result.stderr)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
                finally:
                    self.project, self.memory = old_project, old_memory


if __name__ == "__main__":
    unittest.main()
