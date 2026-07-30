from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
HELPER = ROOT / "scripts/teamwork-case-migration.py"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_case_migration_contract")


def legacy_index() -> dict[str, object]:
    return {
        "schema_version": 1,
        "last_updated": "2026-07-30",
        "project": {"name": "Teamwork", "root": ".", "description": "legacy"},
        "active": {
            "current": "docs/teamwork/current.md",
            "design": None,
            "plan": None,
            "progress": None,
            "report": None,
            "results": [],
            "collaborate": None,
        },
        "entries": [
            {
                "topic": "legacy",
                "kind": "report",
                "title": "Legacy",
                "status": "historical",
                "currentness": "historical",
                "authority": "historical",
                "path": "docs/teamwork/current.md",
                "updated": "2026-07-30",
                "summary": "Legacy",
            }
        ],
    }


class CaseMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        (self.memory / "index.json").write_text(json.dumps(legacy_index(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.memory / "current.md").write_text("# Current\n", encoding="utf-8")
        (self.memory / "README.md").write_text("# README\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def cli(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, text=True, capture_output=True, env=merged, check=False)

    def helper(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(HELPER), *args], cwd=ROOT, text=True, capture_output=True, check=False)

    def request(self, operation: str = "approve-baseline") -> dict[str, object]:
        result = self.cli(
            "migration-request",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps({"schema_version": 1, "operation": operation, "migration_seed": "44" * 32}),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def apply(self, request: dict[str, object]) -> dict[str, object]:
        result = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(request))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def next_request(self, operation: str, migration_id: str, baseline_digest: str) -> dict[str, object]:
        payload = CONTRACT["migration_phase_request"](operation, migration_id, baseline_digest)
        if operation == "cutover":
            payload = CONTRACT["migration_phase_request"](
                operation,
                migration_id,
                baseline_digest,
                cutover_authority="missing",
            )
        return payload

    def test_helper_is_read_only_and_reports_request_inputs(self) -> None:
        before = sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob("*"))
        result = self.helper("request-inputs", "--project-root", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["classification"]["mode"], "legacy-v1")
        self.assertIn("baseline", payload)
        constructed = self.request("approve-baseline")
        self.assertEqual(payload["baseline"]["baseline_digest"], constructed["baseline_digest"])
        after = sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob("*"))
        self.assertEqual(before, after)

    def test_migration_request_and_archive_restore_drill_progress_without_cutover(self) -> None:
        approved_request = self.request("approve-baseline")
        approved = self.apply(approved_request)
        self.assertEqual(approved["phase"], "baseline_approved")
        migration_id = approved["migration_id"]
        baseline_digest = approved_request["baseline_digest"]

        archived = self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.assertEqual(archived["phase"], "archive_durable")
        archive_manifest = self.project / f".teamwork/cold-archive/v1/manifests/{migration_id}.json"
        self.assertTrue(archive_manifest.is_file())
        manifest = json.loads(archive_manifest.read_text(encoding="utf-8"))
        self.assertGreater(len(manifest["objects"]), 0)
        for row in manifest["objects"]:
            mode = (self.project / row["object_path"]).stat().st_mode & 0o777
            self.assertEqual(mode, 0o444)

        candidate = self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.assertEqual(candidate["phase"], "candidate_validated")
        drill = self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        self.assertEqual(drill["phase"], "candidate_validated")
        report = self.project / f".teamwork/runtime/migrations/{migration_id}/restore-drill/report.json"
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "passed")

        cutover = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(self.next_request("cutover", migration_id, baseline_digest)),
        )
        self.assertNotEqual(cutover.returncode, 0)
        self.assertEqual(json.loads(cutover.stderr)["category"], "PREWRITE_SAFE")
        self.assertTrue((self.memory / "index.json").is_file())

    def test_cutover_renames_old_tree_installs_candidate_and_cleanup_keeps_archive(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        cutover = self.apply(
            CONTRACT["migration_phase_request"](
                "cutover",
                migration_id,
                baseline_digest,
                cutover_authority="I authorize Teamwork memory cutover",
            )
        )
        self.assertEqual(cutover["phase"], "committed")
        self.assertTrue((self.project / cutover["renamed_old_tree"]).is_dir())
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["schema_version"], 2)
        self.assertEqual(installed["migration"]["phase"], "committed")
        archive_manifest = self.project / f".teamwork/cold-archive/v1/manifests/{migration_id}.json"
        self.assertTrue(archive_manifest.is_file())

        cleanup = self.apply(CONTRACT["migration_phase_request"]("cleanup", migration_id, baseline_digest))
        self.assertEqual(cleanup["phase"], "cleanup_complete")
        self.assertTrue(archive_manifest.is_file())

    def test_reused_migration_request_fails_closed(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        result = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(approved_request))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")

    def test_empty_baseline_request_fails_closed(self) -> None:
        request = self.request("approve-baseline")
        request["baseline"] = {"schema_version": 1, "paths": [], "baseline_digest": CONTRACT["case_digest"]("migration-baseline", [])}
        request["baseline_digest"] = request["baseline"]["baseline_digest"]
        request["request_digest"] = CONTRACT["migration_request_digest"]({
            "schema_version": 1,
            "operation": "approve-baseline",
            "migration_id": request["migration_id"],
            "baseline_digest": request["baseline_digest"],
            "baseline": request["baseline"],
        })
        result = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(request))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline", json.loads(result.stderr)["message"])

    def test_invalid_migration_request_does_not_create_runtime_lock_tree(self) -> None:
        result = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps({"schema_version": 1, "operation": "approve-baseline"}),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.project / ".teamwork").exists())

    def test_archive_materialization_rejects_baseline_mode_drift(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        os.chmod(self.memory / "current.md", 0o600)
        result = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(self.next_request("materialize-archive", migration_id, approved_request["baseline_digest"])),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")

    def test_restore_drill_rejects_archive_object_mode_drift(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        manifest = json.loads((self.project / f".teamwork/cold-archive/v1/manifests/{migration_id}.json").read_text(encoding="utf-8"))
        os.chmod(self.project / manifest["objects"][0]["object_path"], 0o600)
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        result = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(self.next_request("restore-drill", migration_id, baseline_digest)),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "INDETERMINATE")

    def test_teamwork_runtime_symlink_fails_closed_without_external_write(self) -> None:
        shutil_target = Path(self.temporary.name) / "outside"
        shutil_target.mkdir()
        os.symlink(shutil_target, self.project / ".teamwork")
        result = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(self.request("approve-baseline")))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(shutil_target.iterdir()), [])

    def test_non_migration_mutator_is_blocked_during_intermediate_migration(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        inspected = self.cli("case-inspect", "--project-root", str(self.project))
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        revision = json.loads(inspected.stdout)["revision"]
        result = self.cli(
            "case-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(
                {
                    "schema_version": 2,
                    "operation": "create",
                    "expected_revision": revision,
                    "updated_at": "2026-07-30T00:00:00+00:00",
                    "case_seed": "77" * 32,
                    "title": "Blocked",
                    "task_key": "blocked",
                    "aliases": [],
                }
            ),
        )
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stderr)
        self.assertEqual(payload["category"], "PREWRITE_SAFE")
        self.assertIn("migration", payload["message"])


if __name__ == "__main__":
    unittest.main()
