from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
TEMPLATES = ROOT / "templates/teamwork-memory"


class WorkflowArtifactTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (self.memory / name).write_bytes((TEMPLATES / name).read_bytes())

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
            "consumer": "Writer",
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
            "debug": ("report", "report", "docs/teamwork/workflows/debug/2026-07-22-debug-note.md"),
            "review": ("report", "report", "docs/teamwork/workflows/review/2026-07-22-review-note.md"),
            "conclusion": ("result", "results", "docs/teamwork/workflows/conclusion/2026-07-22-conclusion-note.md"),
            "init": ("report", "report", "docs/teamwork/workflows/init/2026-07-22-init-note.md"),
            "update": ("report", "report", "docs/teamwork/workflows/update/2026-07-22-update-note.md"),
        }
        for workflow, (kind, active_slot, path) in expected.items():
            with self.subTest(workflow=workflow):
                temporary = tempfile.TemporaryDirectory()
                try:
                    project = Path(temporary.name) / "project"
                    memory = project / "docs/teamwork"
                    memory.mkdir(parents=True)
                    for name in ("index.json", "current.md", "README.md"):
                        (memory / name).write_bytes((TEMPLATES / name).read_bytes())
                    original_project = self.project
                    original_memory = self.memory
                    self.project = project
                    self.memory = memory
                    created = self.create(workflow=workflow, slug=f"{workflow}-note", title=f"{workflow.title()} note")
                    self.assertEqual(created["path"], path)
                    text = (project / path).read_text(encoding="utf-8")
                    self.assertIn(f"Artifact Kind: {kind}\nArtifact Type: workflow-artifact\nWorkflow: {workflow}", text)
                    self.assertIn("Consumer: Writer\nSource Revision: source-revision-1\n\n#", text)
                    index = self.index()
                    entry = next(item for item in index["entries"] if item["path"] == path)
                    self.assertEqual(entry["kind"], kind)
                    self.assertEqual(entry["artifact_type"], "workflow-artifact")
                    self.assertEqual(entry["workflow"], workflow)
                    self.assertEqual(entry["consumer"], "Writer")
                    self.assertEqual(entry["applies_to"], ["Writer"])
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

    def test_supersede_moves_results_and_report_singleton_atomically(self) -> None:
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
        self.assertEqual(self.index()["active"]["report"], json.loads(replaced.stdout)["path"])
        old_report = next(item for item in self.index()["entries"] if item["path"] == report["path"])
        self.assertEqual(old_report["authority"], "superseded")

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
        unsafe_memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (unsafe_memory / name).write_bytes((TEMPLATES / name).read_bytes())
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

    def test_active_results_can_hold_multiple_generic_current_entries_but_singletons_do_not(self) -> None:
        research = self.create(workflow="research", slug="research-result", title="Research result")
        conclusion = self.create(workflow="conclusion", slug="conclusion-result", title="Conclusion result")
        active = self.index()["active"]
        self.assertIn(research["path"], active["results"])
        self.assertIn(conclusion["path"], active["results"])

        self.create(workflow="plan", slug="first-plan", title="First plan")
        blocked_plan = self.apply(self.request("create", workflow="plan", slug="second-plan", title="Second plan"))
        self.assert_error(blocked_plan, "active.plan")

        self.create(workflow="debug", slug="first-report", title="First report")
        blocked_report = self.apply(self.request("create", workflow="review", slug="second-report", title="Second report"))
        self.assert_error(blocked_report, "active.report")

    def test_request_is_not_an_arbitrary_index_patch_or_destination_selector(self) -> None:
        request = self.request("create")
        request["destination"] = "docs/teamwork/research/2026-07-22-other.md"
        self.assert_error(self.apply(request), "unsupported keys")

        request = self.request("create")
        request["index_patch"] = [{"op": "replace", "path": "/active/results", "value": []}]
        self.assert_error(self.apply(request), "unsupported keys")


if __name__ == "__main__":
    unittest.main()
