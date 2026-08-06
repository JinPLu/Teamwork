from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MIGRATE = ROOT / "scripts/migrate-teamwork-documents.py"
sys.path.insert(0, str(ROOT / "scripts"))

import teamwork_index_v4 as index_v4  # noqa: E402


def load_migration_helper():
    specification = importlib.util.spec_from_file_location(
        "teamwork_migration_v4", MIGRATE
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


MIGRATION = load_migration_helper()


class TeamworkMigrationV4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.project = self.base / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        (self.memory / "index.json").write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "project": {"name": "Fixture", "root": ".", "description": "legacy cases"},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.original_bodies: dict[str, str] = {}
        for name, body in (
            ("case-alpha", "# Alpha\n\nRecommendation remains explicitly uncertain.\n"),
            ("case-beta", "# Beta\n\nThis source may be consolidated without copying its envelope.\n"),
            ("case-storage", "# Storage only\n\nNo reusable semantic content.\n"),
        ):
            case = self.memory / "cases" / name
            case.mkdir(parents=True)
            (case / "manifest.json").write_text('{"legacy":true}\n', encoding="utf-8")
            (case / "live.md").write_text(body, encoding="utf-8")
            self.original_bodies[name] = body
        self.staging = self.base / "external-staging"
        self.backup = self.base / "external-backup"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_helper(self, command: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(MIGRATE), command, *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def prepare(self) -> None:
        result = self.run_helper(
            "prepare",
            "--project-root",
            str(self.project),
            "--staging-root",
            str(self.staging),
            "--backup-root",
            str(self.backup),
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def write_candidate_and_coverage(self) -> str:
        staged_memory = self.staging / "docs/teamwork"
        index_path = staged_memory / "index.json"
        index = index_v4.load_index(index_path)
        index_v4.register_task(
            index,
            task_key="legacy-teamwork-migration",
            title="Legacy Teamwork migration",
            summary="Reusable legacy meaning is represented by the staged typed document.",
            search_terms=["legacy migration", "typed documents"],
        )
        discussion = index_v4.document_path("discussion", "2026-08-06", "legacy-decision-context")
        target = self.staging / discussion
        target.parent.mkdir(parents=True)
        candidate_body = "# Migrated decision context\n\nWriter supplied this semantic transformation.\n"
        target.write_text(candidate_body, encoding="utf-8")
        index_v4.register_document(
            index,
            task_key="legacy-teamwork-migration",
            document_type="discussion",
            path=discussion,
            status="final",
        )
        index_v4.write_index(index_path, index)
        coverage = {
            "source_cases": [
                {
                    "source_case": "docs/teamwork/cases/case-alpha",
                    "disposition": "migrated",
                    "documents": [discussion],
                },
                {
                    "source_case": "docs/teamwork/cases/case-beta",
                    "disposition": "consolidated",
                    "documents": [discussion],
                },
                {
                    "source_case": "docs/teamwork/cases/case-storage",
                    "disposition": "obsolete-storage-only",
                    "documents": [],
                },
            ]
        }
        (self.staging / "coverage.json").write_text(
            json.dumps(coverage, indent=2) + "\n",
            encoding="utf-8",
        )
        return candidate_body

    def test_inventory_prepare_cutover_readback_and_rollback(self) -> None:
        inventory = self.run_helper("inventory", "--project-root", str(self.project))
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        report = json.loads(inventory.stdout)
        self.assertEqual(report["source_count"], 3)
        self.assertTrue(report["writer_required"])
        self.assertTrue(report["reviewer_required"])
        file_entries = [
            entry for entry in report["source_entries"] if entry["type"] == "file"
        ]
        directory_entries = [
            entry for entry in report["source_entries"] if entry["type"] == "directory"
        ]
        self.assertTrue(file_entries)
        self.assertTrue(all(set(entry) == {"path", "type", "size", "mtime_ns"} for entry in file_entries))
        self.assertTrue(all(set(entry) == {"path", "type"} for entry in directory_entries))

        self.prepare()
        self.assertEqual(
            (self.backup / "docs/teamwork/cases/case-alpha/live.md").read_text(encoding="utf-8"),
            self.original_bodies["case-alpha"],
        )
        initial_coverage = self.run_helper(
            "validate-coverage", "--staging-root", str(self.staging)
        )
        self.assertNotEqual(initial_coverage.returncode, 0)
        self.assertIn("invalid disposition", initial_coverage.stderr)

        candidate_body = self.write_candidate_and_coverage()
        coverage = self.run_helper(
            "validate-coverage", "--staging-root", str(self.staging)
        )
        self.assertEqual(coverage.returncode, 0, coverage.stderr)
        self.assertEqual(json.loads(coverage.stdout)["source_count"], 3)

        cutover = self.run_helper(
            "cutover",
            "--project-root",
            str(self.project),
            "--staging-root",
            str(self.staging),
        )
        self.assertEqual(cutover.returncode, 0, cutover.stderr)
        self.assertTrue((self.memory / "index.json").is_file())
        self.assertFalse((self.memory / "cases").exists())
        self.assertEqual(
            (self.memory / "discussions/2026-08-06-legacy-decision-context.md").read_text(encoding="utf-8"),
            candidate_body,
        )
        self.assertTrue((self.backup / "docs/teamwork/cases/case-beta/live.md").is_file())

        readback = self.run_helper(
            "readback",
            "--project-root",
            str(self.project),
            "--staging-root",
            str(self.staging),
        )
        self.assertEqual(readback.returncode, 0, readback.stderr)
        self.assertEqual(json.loads(readback.stdout)["registered_documents"], 1)
        self.assertTrue(json.loads(readback.stdout)["reviewer_required"])

        rollback = self.run_helper(
            "rollback",
            "--project-root",
            str(self.project),
            "--staging-root",
            str(self.staging),
        )
        self.assertEqual(rollback.returncode, 0, rollback.stderr)
        self.assertEqual(
            json.loads((self.memory / "index.json").read_text(encoding="utf-8"))["schema_version"],
            3,
        )
        for name, body in self.original_bodies.items():
            self.assertEqual(
                (self.memory / "cases" / name / "live.md").read_text(encoding="utf-8"),
                body,
            )
        self.assertTrue((self.backup / "docs/teamwork/index.json").is_file())

    def test_coverage_registration_and_path_boundaries_fail_closed(self) -> None:
        inside = self.run_helper(
            "prepare",
            "--project-root",
            str(self.project),
            "--staging-root",
            str(self.project / "staging"),
            "--backup-root",
            str(self.backup),
        )
        self.assertNotEqual(inside.returncode, 0)
        self.assertIn("external to the project", inside.stderr)
        self.assertFalse(self.backup.exists())

        unsafe = self.memory / "cases/case-alpha/escape"
        unsafe.symlink_to(self.base)
        inventory = self.run_helper("inventory", "--project-root", str(self.project))
        self.assertNotEqual(inventory.returncode, 0)
        self.assertIn("unsafe directory", inventory.stderr)
        unsafe.unlink()

        (self.memory / "reviews").mkdir()
        mixed = self.run_helper("inventory", "--project-root", str(self.project))
        self.assertNotEqual(mixed.returncode, 0)
        self.assertIn("mixed legacy and schema-v4", mixed.stderr)
        (self.memory / "reviews").rmdir()

        self.prepare()
        self.write_candidate_and_coverage()
        coverage_path = self.staging / "coverage.json"
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage["source_cases"][0]["documents"] = [
            "docs/teamwork/reviews/2026-08-06-not-registered.md"
        ]
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
        invalid = self.run_helper(
            "validate-coverage", "--staging-root", str(self.staging)
        )
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("unregistered typed document", invalid.stderr)

    def test_source_metadata_change_stops_before_swap(self) -> None:
        self.prepare()
        self.write_candidate_and_coverage()
        source = self.memory / "cases/case-alpha/live.md"
        before = source.stat()
        changed = self.original_bodies["case-alpha"].replace("uncertain", "unsettled")
        self.assertEqual(len(changed), len(self.original_bodies["case-alpha"]))
        source.write_text(changed, encoding="utf-8")
        os.utime(
            source,
            ns=(before.st_atime_ns, max(before.st_mtime_ns + 1_000_000, source.stat().st_mtime_ns)),
        )

        result = self.run_helper(
            "cutover",
            "--project-root",
            str(self.project),
            "--staging-root",
            str(self.staging),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source file metadata or path inventory changed after staging", result.stderr)
        self.assertEqual(source.read_text(encoding="utf-8"), changed)
        self.assertFalse((self.project / "docs/.teamwork-migration-new").exists())
        self.assertFalse((self.project / "docs/.teamwork-migration-old").exists())

    def test_swap_leftovers_and_copy_or_replace_failures_restore_active_tree(self) -> None:
        self.prepare()
        self.write_candidate_and_coverage()
        docs = self.project / "docs"
        memory = docs / "teamwork"
        new_tree = docs / MIGRATION.SWAP_NEW_NAME
        old_tree = docs / MIGRATION.SWAP_OLD_NAME

        new_tree.mkdir()
        leftover = self.run_helper(
            "cutover",
            "--project-root",
            str(self.project),
            "--staging-root",
            str(self.staging),
        )
        self.assertNotEqual(leftover.returncode, 0)
        self.assertIn("swap path must not already exist", leftover.stderr)
        self.assertTrue((memory / "cases/case-alpha/live.md").is_file())
        new_tree.rmdir()

        real_copytree = MIGRATION.shutil.copytree

        def fail_candidate_copy(source: Path, destination: Path, *args, **kwargs):
            if Path(destination) == new_tree:
                Path(destination).mkdir()
                (Path(destination) / "partial").write_text("partial\n", encoding="utf-8")
                raise OSError("injected candidate copy failure")
            return real_copytree(source, destination, *args, **kwargs)

        with mock.patch.object(MIGRATION.shutil, "copytree", side_effect=fail_candidate_copy):
            with self.assertRaisesRegex(MIGRATION.MigrationError, "original Teamwork tree remains active"):
                MIGRATION.cutover(self.project, self.staging)
        self.assertTrue((memory / "cases/case-alpha/live.md").is_file())
        self.assertFalse(new_tree.exists())
        self.assertFalse(old_tree.exists())

        MIGRATION.cutover(self.project, self.staging)
        self.assertEqual(
            json.loads((memory / "index.json").read_text(encoding="utf-8"))["schema_version"],
            4,
        )
        real_replace = MIGRATION.os.replace

        def fail_backup_activation(source: Path, destination: Path) -> None:
            if Path(source) == new_tree and Path(destination) == memory:
                raise OSError("injected replacement failure")
            real_replace(source, destination)

        with mock.patch.object(MIGRATION.os, "replace", side_effect=fail_backup_activation):
            with self.assertRaisesRegex(MIGRATION.MigrationError, "schema-v4 Teamwork tree remains active"):
                MIGRATION.rollback(self.project, self.staging)
        self.assertEqual(
            json.loads((memory / "index.json").read_text(encoding="utf-8"))["schema_version"],
            4,
        )
        self.assertFalse(new_tree.exists())
        self.assertFalse(old_tree.exists())


if __name__ == "__main__":
    unittest.main()
