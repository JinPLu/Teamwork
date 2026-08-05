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
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_case_archive_recovery_contract")


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


class CaseArchiveRecoveryTests(unittest.TestCase):
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

    def test_interrupted_archive_materialization_recovers_from_runtime_journal(self) -> None:
        request = {
            "schema_version": 1,
            "operation": "approve-baseline",
            "migration_seed": "55" * 32,
        }
        constructed = self.cli("migration-request", "--project-root", str(self.project), "--request-json", json.dumps(request))
        self.assertEqual(constructed.returncode, 0, constructed.stderr)
        approved_request = json.loads(constructed.stdout)
        approved = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(approved_request))
        self.assertEqual(approved.returncode, 0, approved.stderr)
        approved_payload = json.loads(approved.stdout)
        migration_id = approved_payload["migration_id"]
        archive_request = CONTRACT["migration_phase_request"]("materialize-archive", migration_id, approved_request["baseline_digest"])
        interrupted = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(archive_request),
            env={"TEAMWORK_ARTIFACT_TRANSACTION_INTERRUPT_AFTER_BACKUP": "1"},
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(json.loads(interrupted.stderr)["category"], "INDETERMINATE")
        marker = self.project / f".teamwork/runtime/migrations/{migration_id}/.transaction.json"
        self.assertTrue(marker.is_file())

        replay = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(archive_request))
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["phase"], "archive_durable")
        self.assertFalse(marker.exists())
        archive_manifest = self.project / f".teamwork/runtime/migrations/{migration_id}/backup/manifest.json"
        self.assertTrue(archive_manifest.is_file())

    def test_cutover_recover_continues_after_old_tree_rename_failpoint(self) -> None:
        constructed = self.cli(
            "migration-request",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps({"schema_version": 1, "operation": "approve-baseline", "migration_seed": "66" * 32}),
        )
        self.assertEqual(constructed.returncode, 0, constructed.stderr)
        approved_request = json.loads(constructed.stdout)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        for request in (
            approved_request,
            CONTRACT["migration_phase_request"]("materialize-archive", migration_id, baseline_digest),
            CONTRACT["migration_phase_request"]("prepare-candidate", migration_id, baseline_digest),
            CONTRACT["migration_phase_request"]("restore-drill", migration_id, baseline_digest),
        ):
            result = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(request))
            self.assertEqual(result.returncode, 0, result.stderr)
        cutover = CONTRACT["migration_phase_request"](
            "cutover",
            migration_id,
            baseline_digest,
            cutover_authority="I authorize Teamwork memory cutover",
        )
        interrupted = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(cutover),
            env={"TEAMWORK_MIGRATION_FAILPOINT": "after-old-tree-renamed"},
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(json.loads(interrupted.stderr)["category"], "INDETERMINATE")
        self.assertFalse((self.project / "docs/teamwork").exists())
        self.assertTrue((self.project / f".teamwork/runtime/migrations/{migration_id}/renamed-old/docs-teamwork").is_dir())

        recovered = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(cutover))
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        payload = json.loads(recovered.stdout)
        self.assertEqual(payload["phase"], "committed")
        self.assertTrue((self.project / "docs/teamwork/index.json").is_file())
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["migration"]["phase"], "committed")

        recover_again = self.cli("migration-recover", "--project-root", str(self.project), "--migration-id", migration_id)
        self.assertEqual(recover_again.returncode, 0, recover_again.stderr)
        self.assertEqual(json.loads(recover_again.stdout)["phase"], "committed")

    def test_cutover_recover_continues_when_rename_completed_before_journal_update(self) -> None:
        constructed = self.cli(
            "migration-request",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps({"schema_version": 1, "operation": "approve-baseline", "migration_seed": "77" * 32}),
        )
        self.assertEqual(constructed.returncode, 0, constructed.stderr)
        approved_request = json.loads(constructed.stdout)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        for request in (
            approved_request,
            CONTRACT["migration_phase_request"]("materialize-archive", migration_id, baseline_digest),
            CONTRACT["migration_phase_request"]("prepare-candidate", migration_id, baseline_digest),
            CONTRACT["migration_phase_request"]("restore-drill", migration_id, baseline_digest),
        ):
            result = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(request))
            self.assertEqual(result.returncode, 0, result.stderr)
        cutover = CONTRACT["migration_phase_request"](
            "cutover",
            migration_id,
            baseline_digest,
            cutover_authority="I authorize Teamwork memory cutover",
        )
        interrupted = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(cutover),
            env={"TEAMWORK_MIGRATION_FAILPOINT": "after-old-tree-renamed-before-journal"},
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(json.loads(interrupted.stderr)["category"], "INDETERMINATE")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/cutover-journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["phase"], "prepared")
        self.assertFalse((self.project / "docs/teamwork").exists())
        self.assertTrue((self.project / f".teamwork/runtime/migrations/{migration_id}/renamed-old/docs-teamwork").is_dir())

        recovered = self.cli("migration-apply", "--project-root", str(self.project), "--request-json", json.dumps(cutover))
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertEqual(json.loads(recovered.stdout)["phase"], "committed")


if __name__ == "__main__":
    unittest.main()
