from __future__ import annotations

import json
import os
import re
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_workflow_artifact_contract")


def write_legacy_v1_memory(memory: Path) -> None:
    memory.mkdir(parents=True, exist_ok=True)
    index = {
        "schema_version": 1,
        "last_updated": "2026-07-22",
        "project": {
            "name": "Fixture",
            "root": ".",
            "description": "Local Teamwork memory index for this project.",
        },
        "source_of_truth_order": ["active", "linked", "header_search", "fulltext"],
        "ignore_globs": [".planning/**"],
        "budgets": {"header_first": True},
        "active": {
            "collaborate": None,
            "current": "docs/teamwork/current.md",
            "design": None,
            "plan": None,
            "progress": None,
            "report": None,
            "results": [],
        },
        "collaborate_consumed_sources": [],
        "entries": [
            {
                "topic": "project-initialization",
                "kind": "result",
                "title": "Teamwork project initialization",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": "docs/teamwork/current.md",
                "applies_to": ["AGENTS.md", "docs/teamwork/"],
                "linked": [],
                "evidence_paths": ["docs/teamwork/current.md"],
                "supersedes": [],
                "search_keys": ["teamwork-init", "project-init", "initialization"],
                "updated": "2026-07-22",
                "summary": "Initial ordinary Teamwork memory entry created by project initialization.",
            }
        ],
        "profiles": {
            "status": ["index", "current", "topic"],
            "implementation": ["index", "current", "active_design_or_plan", "linked_research_headers"],
            "review": ["index", "current", "active_design_or_plan", "active_progress", "verification"],
            "research": ["index", "current", "topic_headers", "linked_artifacts"],
            "design": ["index", "current", "accepted_decisions", "active_design_plan", "linked_research"],
        },
        "pending": [],
    }
    (memory / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (memory / "current.md").write_text("# Teamwork Current State\n", encoding="utf-8")
    (memory / "README.md").write_text("# Teamwork Runtime Index README\n", encoding="utf-8")


class WorkflowArtifactTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        write_legacy_v1_memory(self.memory)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def cli(self, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            [sys.executable, str(CLI), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=merged,
            check=False,
        )

    def inspect(self) -> dict[str, object]:
        result = self.cli("artifact-inspect", "--project-root", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def apply(self, request: dict[str, object], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.cli(
            "artifact-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(request),
            env=env,
        )

    def request(
        self,
        operation: str,
        *,
        workflow: str = "research",
        slug: str = "runtime-evidence",
        title: str = "Runtime evidence",
        updated: str = "2026-07-22",
        previous_path: str | None = None,
        expected_revision: str | None = None,
        body: str = "## Evidence\n\n- Direct local observation.",
        consumer: str = "Writer",
    ) -> dict[str, object]:
        request: dict[str, object] = {
            "schema_version": 1,
            "operation": operation,
            "expected_revision": expected_revision or str(self.inspect()["revision"]),
            "artifact_type": "workflow-artifact",
            "workflow": workflow,
            "slug": slug,
            "title": title,
            "summary": f"{title} summary.",
            "consumer": consumer,
            "source_revision": "source-revision-1",
            "updated": updated,
            "body": body,
            "linked": ["docs/teamwork/current.md"],
            "evidence_paths": ["docs/teamwork/current.md"],
            "search_keys": [workflow, slug],
        }
        if previous_path is not None:
            request["previous_path"] = previous_path
        return request

    def index(self) -> dict[str, object]:
        return json.loads((self.memory / "index.json").read_text(encoding="utf-8"))

    def write_index(self, index: dict[str, object]) -> None:
        (self.memory / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def snapshot(self) -> dict[str, tuple[object, ...]]:
        snapshot: dict[str, tuple[object, ...]] = {}
        for path in sorted((self.project, *self.project.rglob("*")), key=str):
            relative = "." if path == self.project else path.relative_to(self.project).as_posix()
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                snapshot[relative] = ("file", stat.S_IMODE(info.st_mode), path.read_bytes())
            elif stat.S_ISDIR(info.st_mode):
                snapshot[relative] = ("dir", stat.S_IMODE(info.st_mode))
            elif stat.S_ISLNK(info.st_mode):
                snapshot[relative] = ("symlink", os.readlink(path))
        return snapshot

    def assert_error(self, result: subprocess.CompletedProcess[str], pattern: str | None = None) -> None:
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stderr)
        self.assertEqual(payload["category"], "PREWRITE_SAFE")
        if pattern is not None:
            self.assertRegex(payload["message"], pattern)

    def create(self, **kwargs: object) -> dict[str, object]:
        result = self.apply(self.request("create", **kwargs))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_schema_and_cli_surface_are_closed(self) -> None:
        schema = self.cli("artifact-schema", "create")
        self.assertEqual(schema.returncode, 0, schema.stderr)
        payload = json.loads(schema.stdout)
        self.assertEqual(payload["artifact_type"], "workflow-artifact")
        self.assertEqual(payload["expected_revision"], "<revision from artifact-inspect>")
        self.assertNotIn("destination", payload)

        bad = self.cli("artifact-schema", "close")
        self.assertNotEqual(bad.returncode, 0)
        inspected = self.inspect()
        self.assertRegex(str(inspected["revision"]), r"^[0-9a-f]{64}$")
        self.assertEqual(inspected["active"]["registrations"], [])

    def test_create_derive_paths_headers_and_index_fields_for_every_workflow(self) -> None:
        expected = {
            "research": ("research", "results", "docs/teamwork/research/2026-07-22-research-note.md"),
            "plan": ("plan", "plan", "docs/teamwork/plans/2026-07-22-plan-note.md"),
            "debug": ("report", "results", "docs/teamwork/workflows/debug/2026-07-22-debug-note.md"),
            "review": ("report", "results", "docs/teamwork/workflows/review/2026-07-22-review-note.md"),
            "execution": ("result", "results", "docs/teamwork/workflows/execution/2026-07-22-execution-note.md"),
            "conclusion": ("result", "results", "docs/teamwork/workflows/conclusion/2026-07-22-conclusion-note.md"),
            "init": ("report", "results", "docs/teamwork/workflows/init/2026-07-22-init-note.md"),
            "update": ("report", "results", "docs/teamwork/workflows/update/2026-07-22-update-note.md"),
        }
        for workflow, (kind, active_slot, path) in expected.items():
            with self.subTest(workflow=workflow):
                temporary = tempfile.TemporaryDirectory()
                try:
                    project = Path(temporary.name) / "project"
                    memory = project / "docs/teamwork"
                    write_legacy_v1_memory(memory)
                    original_project = self.project
                    original_memory = self.memory
                    self.project = project
                    self.memory = memory
                    consumer = "Root handoff" if workflow == "execution" else "Writer"
                    created = self.create(
                        workflow=workflow,
                        slug=f"{workflow}-note",
                        title=f"{workflow.title()} note",
                        consumer=consumer,
                    )
                    self.assertEqual(created["path"], path)
                    text = (project / path).read_text(encoding="utf-8")
                    self.assertIn(f"Artifact Kind: {kind}\nArtifact Type: workflow-artifact\nWorkflow: {workflow}", text)
                    self.assertIn(f"Consumer: {consumer}\nSource Revision: source-revision-1\n\n#", text)
                    index = self.index()
                    entry = next(item for item in index["entries"] if item["path"] == path)
                    self.assertEqual(entry["kind"], kind)
                    self.assertEqual(entry["artifact_type"], "workflow-artifact")
                    self.assertEqual(entry["workflow"], workflow)
                    self.assertEqual(entry["consumer"], consumer)
                    self.assertEqual(entry["applies_to"], [consumer])
                    self.assertIn(path, entry["evidence_paths"])
                    if active_slot == "results":
                        self.assertIn(path, index["active"]["results"])
                    else:
                        self.assertEqual(index["active"][active_slot], path)
                finally:
                    self.project = original_project
                    self.memory = original_memory
                    temporary.cleanup()

    def test_update_requires_previous_path_and_keeps_destination(self) -> None:
        created = self.create(workflow="plan", slug="implementation-route", title="Implementation route")
        path = created["path"]
        updated = self.apply(
            self.request(
                "update",
                workflow="plan",
                slug="implementation-route",
                title="Implementation route revised",
                previous_path=path,
                body="## Plan\n\n- Revised direct route.",
            )
        )
        self.assertEqual(updated.returncode, 0, updated.stderr)
        payload = json.loads(updated.stdout)
        self.assertEqual(payload["path"], path)
        text = (self.project / path).read_text(encoding="utf-8")
        self.assertIn("# Implementation route revised\n\n## Plan", text)
        entry = next(item for item in self.index()["entries"] if item["path"] == path)
        self.assertEqual(entry["title"], "Implementation route revised")

        bad = self.apply(
            self.request(
                "update",
                workflow="plan",
                slug="new-implementation-route",
                title="New implementation route",
                previous_path=path,
            )
        )
        self.assert_error(bad, "destination")

    def test_supersede_moves_results_atomically_and_plan_remains_singleton(self) -> None:
        first = self.create(workflow="research", slug="first-result", title="First result")
        second = self.apply(
            self.request(
                "supersede",
                workflow="conclusion",
                slug="final-result",
                title="Final result",
                updated="2026-07-23",
                previous_path=first["path"],
            )
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        second_path = json.loads(second.stdout)["path"]
        index = self.index()
        self.assertNotIn(first["path"], index["active"]["results"])
        self.assertIn(second_path, index["active"]["results"])
        first_entry = next(item for item in index["entries"] if item["path"] == first["path"])
        self.assertEqual(first_entry["status"], "superseded")
        self.assertEqual(first_entry["currentness"], "historical")

        report = self.create(workflow="debug", slug="debug-report", title="Debug report")
        replaced = self.apply(
            self.request(
                "supersede",
                workflow="review",
                slug="review-report",
                title="Review report",
                updated="2026-07-23",
                previous_path=report["path"],
            )
        )
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        replaced_path = json.loads(replaced.stdout)["path"]
        index = self.index()
        self.assertIsNone(index["active"]["report"])
        self.assertNotIn(report["path"], index["active"]["results"])
        self.assertIn(replaced_path, index["active"]["results"])
        old_report = next(item for item in self.index()["entries"] if item["path"] == report["path"])
        self.assertEqual(old_report["authority"], "superseded")

    def test_supersede_migrates_a_current_legacy_plan_and_binds_its_bytes(self) -> None:
        legacy_path = "docs/teamwork/plans/2026-07-19-legacy-plan.md"
        legacy_text = (
            "Artifact Type: plan\n"
            "Last Updated: 2026-07-19\n\n"
            "# Legacy plan\n\n"
            "## Steps\n\n"
            "- Preserve this historical body.\n"
        )
        target = self.project / legacy_path
        target.parent.mkdir(parents=True)
        target.write_text(legacy_text, encoding="utf-8")
        index = self.index()
        index["active"]["plan"] = legacy_path
        index["entries"].append(
            {
                "topic": "legacy-plan",
                "kind": "plan",
                "title": "Legacy plan",
                "status": "accepted",
                "currentness": "current",
                "authority": "active-summary",
                "path": legacy_path,
                "linked": [],
                "evidence_paths": [legacy_path],
                "supersedes": [],
                "search_keys": ["legacy-plan"],
                "updated": "2026-07-19",
                "summary": "Legacy plan summary.",
            }
        )
        self.write_index(index)

        inspected = self.inspect()
        migrated = self.apply(
            self.request(
                "supersede",
                workflow="plan",
                slug="current-plan",
                title="Current plan",
                updated="2026-07-28",
                previous_path=legacy_path,
                expected_revision=str(inspected["revision"]),
                body="## Plan\n\n- Use the current transaction route.",
            )
        )
        self.assertEqual(migrated.returncode, 0, migrated.stderr)
        payload = json.loads(migrated.stdout)
        current_path = "docs/teamwork/plans/2026-07-28-current-plan.md"
        self.assertEqual(payload["path"], current_path)
        self.assertEqual((self.project / legacy_path).read_text(encoding="utf-8"), legacy_text)
        current_index = self.index()
        self.assertEqual(current_index["active"]["plan"], current_path)
        legacy_entry = next(item for item in current_index["entries"] if item["path"] == legacy_path)
        self.assertEqual(
            (legacy_entry["status"], legacy_entry["currentness"], legacy_entry["authority"]),
            ("superseded", "historical", "superseded"),
        )
        self.assertEqual(legacy_entry["superseded_by"], current_path)
        current_entry = next(item for item in current_index["entries"] if item["path"] == current_path)
        self.assertEqual(current_entry["workflow"], "plan")
        self.assertEqual(current_entry["supersedes"], [legacy_path])

        stale_project = Path(self.temporary.name) / "stale-project"
        stale_memory = stale_project / "docs/teamwork"
        write_legacy_v1_memory(stale_memory)
        stale_target = stale_project / legacy_path
        stale_target.parent.mkdir(parents=True)
        stale_target.write_text(legacy_text, encoding="utf-8")
        stale_index = json.loads((stale_memory / "index.json").read_text(encoding="utf-8"))
        stale_index["active"]["plan"] = legacy_path
        stale_index["entries"].append(index["entries"][-1])
        (stale_memory / "index.json").write_text(
            json.dumps(stale_index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        original_project = self.project
        original_memory = self.memory
        try:
            self.project = stale_project
            self.memory = stale_memory
            stale_revision = str(self.inspect()["revision"])
            stale_target.write_text(legacy_text + "\nUnindexed drift.\n", encoding="utf-8")
            rejected = self.apply(
                self.request(
                    "supersede",
                    workflow="plan",
                    slug="current-plan",
                    title="Current plan",
                    updated="2026-07-28",
                    previous_path=legacy_path,
                    expected_revision=stale_revision,
                )
            )
            self.assert_error(rejected, "stale")
        finally:
            self.project = original_project
            self.memory = original_memory

    def test_stale_revision_and_active_byte_tampering_are_rejected(self) -> None:
        created = self.create()
        stale = self.apply(self.request("update", previous_path=created["path"], expected_revision="0" * 64))
        self.assert_error(stale, "stale|expected_revision")

        inspected = self.inspect()
        path = self.project / created["path"]
        path.write_text(path.read_text(encoding="utf-8") + "\nTampered.\n", encoding="utf-8")
        tampered = self.apply(self.request("update", previous_path=created["path"], expected_revision=str(inspected["revision"])))
        self.assert_error(tampered, "stale")

    def test_collision_managed_workflow_and_unsafe_paths_fail_closed(self) -> None:
        collision = self.project / "docs/teamwork/research/2026-07-22-runtime-evidence.md"
        collision.parent.mkdir(parents=True)
        collision.write_text("existing", encoding="utf-8")
        self.assert_error(self.apply(self.request("create")), "destination")

        managed = self.request("create", workflow="research")
        managed["workflow"] = "design"
        self.assert_error(self.apply(managed), "specialized")

        self.create(workflow="plan", slug="controlled-path", title="Controlled path")
        bad_previous = self.request("update", workflow="plan", slug="controlled-path", title="Controlled path", previous_path="docs/teamwork/design/2026-07-22-controlled-path.md")
        self.assert_error(self.apply(bad_previous), "previous_path")

        unsafe_project = Path(self.temporary.name) / "unsafe"
        unsafe_memory = unsafe_project / "docs/teamwork"
        write_legacy_v1_memory(unsafe_memory)
        target = unsafe_project / "docs/teamwork/research/2026-07-22-runtime-evidence.md"
        target.parent.mkdir(parents=True)
        os.symlink(unsafe_project / "outside.md", target)
        original_project = self.project
        original_memory = self.memory
        try:
            self.project = unsafe_project
            self.memory = unsafe_memory
            self.assert_error(self.apply(self.request("create")), "same-device|non-symlink|regular")
        finally:
            self.project = original_project
            self.memory = original_memory

    def test_atomic_recovery_restores_exact_preimage_after_interruption(self) -> None:
        created = self.create()
        before = self.snapshot()
        failed = self.apply(
            self.request(
                "update",
                previous_path=created["path"],
                title="Interrupted evidence",
                body="## Evidence\n\n- Interrupted update.",
            ),
            env={"TEAMWORK_ARTIFACT_TRANSACTION_INTERRUPT_AFTER_BACKUP": "1"},
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(json.loads(failed.stderr)["category"], "INDETERMINATE")
        marker = self.memory / ".workflow-artifact-transaction.json"
        self.assertTrue(marker.is_file())

        recovered = self.inspect()

        self.assertTrue(recovered["recovered"])
        self.assertFalse(marker.exists())
        self.assertEqual(self.snapshot(), before)

    def test_active_results_can_hold_multiple_generic_current_entries_but_plan_does_not(self) -> None:
        research = self.create(workflow="research", slug="research-result", title="Research result")
        conclusion = self.create(workflow="conclusion", slug="conclusion-result", title="Conclusion result")
        update = self.create(workflow="update", slug="update-receipt", title="Update receipt")
        review = self.create(workflow="review", slug="review-verdict", title="Review verdict")
        active = self.index()["active"]
        self.assertIn(research["path"], active["results"])
        self.assertIn(conclusion["path"], active["results"])
        self.assertIn(update["path"], active["results"])
        self.assertIn(review["path"], active["results"])
        self.assertIsNone(active["report"])

        self.create(workflow="plan", slug="first-plan", title="First plan")
        blocked_plan = self.apply(self.request("create", workflow="plan", slug="second-plan", title="Second plan"))
        self.assert_error(blocked_plan, "active.plan")

    def test_execution_is_one_terminal_handoff_and_active_goal_suppresses_it(self) -> None:
        rejected_consumer = self.apply(
            self.request(
                "create",
                workflow="execution",
                slug="terminal-handoff",
                title="Terminal handoff",
            )
        )
        self.assert_error(rejected_consumer, "real downstream consumer")

        created = self.create(
            workflow="execution",
            slug="terminal-handoff",
            title="Terminal handoff",
            consumer="Root",
        )
        update = self.apply(
            self.request(
                "update",
                workflow="execution",
                slug="terminal-handoff",
                title="Incremental progress",
                previous_path=created["path"],
                consumer="Root",
            )
        )
        self.assert_error(update, "one terminal handoff")

        temporary = tempfile.TemporaryDirectory()
        original_project = self.project
        original_memory = self.memory
        try:
            project = Path(temporary.name) / "project"
            memory = project / "docs/teamwork"
            write_legacy_v1_memory(memory)
            self.project = project
            self.memory = memory
            goal = {
                "schema_version": 1,
                "artifact_type": "goal",
                "slug": "finish-run",
                "title": "Finish run",
                "objective": "Finish the verified execution.",
                "scope": {"included": ["Execution"]},
                "protected_boundaries": ["No release."],
                "invariants": ["Keep direct evidence."],
                "success_signal": "The execution path passes.",
                "budget": {"token_budget": 1000},
                "hard_stops": ["Missing authority."],
                "status": "active",
                "current_unmet_claim": "The execution path has not passed.",
                "started_at": "2026-07-22",
                "updated": "2026-07-22",
                "next_strategy": "Run the direct path.",
                "attempts": [],
                "state_revision": 1,
                "closure": None,
            }
            goal_path = CONTRACT["goal_path"](goal)
            target = project / goal_path
            target.parent.mkdir(parents=True)
            target.write_text(CONTRACT["render_goal_artifact"](goal), encoding="utf-8")
            index = self.index()
            index["active"]["progress"] = goal_path
            index["entries"].append(
                {
                    "topic": "finish-run",
                    "kind": "progress",
                    "title": "Finish run",
                    "status": "active",
                    "currentness": "current",
                    "authority": "canonical",
                    "path": goal_path,
                    "linked": [],
                    "evidence_paths": [goal_path],
                    "supersedes": [],
                    "search_keys": ["finish-run"],
                    "updated": "2026-07-22",
                    "summary": "Finish the verified execution.",
                }
            )
            self.write_index(index)
            blocked = self.apply(
                self.request(
                    "create",
                    workflow="execution",
                    slug="duplicate-progress",
                    title="Duplicate progress",
                    consumer="Root",
                )
            )
            self.assert_error(blocked, "active Goal owns execution progress")
        finally:
            self.project = original_project
            self.memory = original_memory
            temporary.cleanup()

    def test_legacy_workflow_report_slot_is_inspected_and_migrated_on_apply(self) -> None:
        update = self.create(workflow="update", slug="update-receipt", title="Update receipt")
        update_path = update["path"]
        legacy = self.index()
        legacy["active"]["results"].remove(update_path)
        legacy["active"]["report"] = update_path
        self.write_index(legacy)

        inspected = self.inspect()
        self.assertIsNone(inspected["active"]["report"])
        self.assertIn(update_path, inspected["active"]["results"])
        update_registration = next(item for item in inspected["active"]["registrations"] if item["path"] == update_path)
        self.assertEqual(update_registration["active"], "results")

        applied = self.apply(
            self.request(
                "create",
                workflow="review",
                slug="review-verdict",
                title="Review verdict",
                updated="2026-07-23",
                expected_revision=str(inspected["revision"]),
            )
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        payload = json.loads(applied.stdout)
        review_path = payload["path"]
        self.assertEqual(set(payload["changed_paths"]), {review_path, "docs/teamwork/index.json"})
        index = self.index()
        self.assertIsNone(index["active"]["report"])
        self.assertIn(update_path, index["active"]["results"])
        self.assertIn(review_path, index["active"]["results"])
        update_entry = next(item for item in index["entries"] if item["path"] == update_path)
        self.assertEqual(update_entry["status"], "active")
        self.assertEqual(update_entry["currentness"], "current")
        self.assertEqual(update_entry["authority"], "canonical")

    def test_legacy_workflow_report_slot_still_enforces_revision_and_currentness(self) -> None:
        update = self.create(workflow="update", slug="update-receipt", title="Update receipt")
        update_path = update["path"]
        legacy = self.index()
        legacy["active"]["results"].remove(update_path)
        legacy["active"]["report"] = update_path
        self.write_index(legacy)

        stale = self.apply(
            self.request(
                "create",
                workflow="review",
                slug="stale-review",
                title="Stale review",
                updated="2026-07-23",
                expected_revision="0" * 64,
            )
        )
        self.assert_error(stale, "stale|expected_revision")

        artifact = self.project / update_path
        artifact.write_text(artifact.read_text(encoding="utf-8").replace("# Update receipt", "# Tampered receipt", 1), encoding="utf-8")
        inspected = self.cli("artifact-inspect", "--project-root", str(self.project))
        self.assert_error(inspected, "do(?:es)? not agree")

    def test_non_workflow_report_pointer_is_not_moved(self) -> None:
        report_path = "docs/teamwork/reports/manual-report.md"
        report = self.project / report_path
        report.parent.mkdir(parents=True)
        report.write_text("# Manual report\n", encoding="utf-8")
        index = self.index()
        index["active"]["report"] = report_path
        index["entries"].append(
            {
                "topic": "manual-report",
                "kind": "report",
                "title": "Manual report",
                "status": "active",
                "currentness": "current",
                "authority": "supporting",
                "path": report_path,
                "linked": [],
                "evidence_paths": [report_path],
                "supersedes": [],
                "search_keys": ["manual-report"],
                "updated": "2026-07-22",
                "summary": "Manual report summary.",
            }
        )
        self.write_index(index)

        inspected = self.inspect()
        self.assertEqual(inspected["active"]["report"], report_path)
        self.assertEqual(inspected["active"]["results"], [])
        self.assertEqual(inspected["active"]["registrations"], [])

    def test_request_is_not_an_arbitrary_index_patch_or_destination_selector(self) -> None:
        request = self.request("create")
        request["destination"] = "docs/teamwork/research/2026-07-22-other.md"
        self.assert_error(self.apply(request), "unsupported keys")

        request = self.request("create")
        request["index_patch"] = [{"op": "replace", "path": "/active/results", "value": []}]
        self.assert_error(self.apply(request), "unsupported keys")


if __name__ == "__main__":
    unittest.main()
