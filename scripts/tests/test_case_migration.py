from __future__ import annotations

import hashlib
import json
import os
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
HELPER = ROOT / "scripts/teamwork-case-migration.py"
INIT_SH = ROOT / "scripts/init-project.sh"
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


def tree_fingerprint(root: Path) -> dict[str, dict[str, object]]:
    if not root.exists():
        return {}
    fingerprint: dict[str, dict[str, object]] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISREG(info.st_mode):
            fingerprint[rel] = {"type": "file", "mode": mode, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        elif stat.S_ISDIR(info.st_mode):
            fingerprint[rel] = {"type": "dir", "mode": mode}
        elif stat.S_ISLNK(info.st_mode):
            fingerprint[rel] = {"type": "symlink", "mode": mode, "target": os.readlink(path)}
        else:
            fingerprint[rel] = {"type": "other", "mode": mode}
    return fingerprint


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

    def helper(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run([sys.executable, str(HELPER), *args], cwd=ROOT, text=True, capture_output=True, env=merged, check=False)

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

    def candidate_path(self, migration_id: str, logical_path: str) -> Path:
        prefix = "docs/teamwork/"
        self.assertTrue(logical_path.startswith(prefix), logical_path)
        return self.project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/{logical_path.removeprefix(prefix)}"

    def test_legacy_grill_discussion_maps_to_brainstorm_questions_not_runtime_frontier(self) -> None:
        discussion = CONTRACT["normalize_discussion_state"](
            {
                "schema_version": 3,
                "artifact_type": "discussion",
                "slug": "legacy-grill",
                "title": "Legacy Grill",
                "updated": "2026-07-30",
                "status": "active",
                "superseded_by": None,
                "mode": "grill",
                "goal": "Map legacy grill without retaining runtime grill.",
                "current_branch": "Challenge the boundary.",
                "return_path": "Continue through Collaborate.",
                "convergence": "Use brainstorm semantics.",
                "blockers": [],
                "key_evidence": ["Legacy source is preserved."],
                "settled": [],
                "synthesis": ["Legacy grill checkpoint."],
                "tensions": [],
                "frontier": [
                    {
                        "id": "Q1",
                        "title": "Boundary",
                        "level": "boundary",
                        "status": "current",
                        "prompt": "Which boundary changes the result?",
                        "options": [
                            {"id": "a", "label": "Route A", "tradeoff": "Fast."},
                            {"id": "b", "label": "Route B", "tradeoff": "Careful."},
                        ],
                        "recommendation": "b",
                        "largest_downside": "Choosing too early.",
                        "why_critical": "This blocks planning.",
                        "blocks": [],
                        "depends_on": [],
                        "closure_signal": "One route is selected.",
                        "resolution": None,
                    }
                ],
                "current_batch": ["Q1"],
            }
        )

        mapped = CONTRACT["_map_discussion_to_collaborate"](discussion)

        self.assertEqual(mapped["mode"], "brainstorm")
        self.assertEqual(mapped["frontier"], [])
        self.assertEqual(mapped["current_batch"], ["discussion-question-Q1"])
        self.assertEqual(mapped["questions"][0]["id"], "discussion-question-Q1")
        self.assertEqual(mapped["questions"][0]["status"], "open")
        self.assertIn("Which boundary changes the result?", mapped["questions"][0]["prompt"])
        normalized = CONTRACT["normalize_collaborate_state"]({key: value for key, value in mapped.items() if not key.startswith("_")})
        self.assertEqual(normalized["mode"], "brainstorm")

    def test_case_v2_migration_preserves_legacy_grill_as_brainstorm_evidence_only(self) -> None:
        collaborate_path = "docs/teamwork/collaborate/current.md"
        (self.memory / "collaborate").mkdir(parents=True)
        (self.project / collaborate_path).write_text(
            "Artifact Kind: collaborate\n"
            "Mode: grill\n\n"
            "# Legacy Grill Checkpoint\n\n"
            "Questions from the retired grill workflow stay as preserved evidence.\n",
            encoding="utf-8",
        )
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        index["active"]["collaborate"] = None
        index["entries"].append(
            {
                "topic": "legacy-grill",
                "kind": "result",
                "title": "Legacy Grill Checkpoint",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": collaborate_path,
                "updated": "2026-07-30",
                "summary": "Retired grill checkpoint.",
            }
        )
        (self.memory / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))

        candidate_index = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/index.json").read_text(encoding="utf-8"))
        case_row = next(row for row in candidate_index["active_cases"] if row["task_key"] == "legacy-grill")
        manifest = json.loads(self.candidate_path(migration_id, case_row["manifest_path"]).read_text(encoding="utf-8"))
        artifact_id = next(artifact_id for artifact_id, row in manifest["artifacts"].items() if row["role"] == "collaborate")
        artifact_path = manifest["artifacts"][artifact_id]["path"]
        artifact_text = self.candidate_path(migration_id, artifact_path).read_text(encoding="utf-8")

        self.assertEqual(case_row["phase"], "collaborating")
        self.assertIn("- Migrated mode: `brainstorm`", artifact_text)
        self.assertIn("- Challenge evidence: preserved from the legacy grill checkpoint.", artifact_text)
        self.assertIn("Mode: grill", artifact_text)
        self.assertNotIn('"mode": "grill"', artifact_text)

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

    def test_helper_rejects_leaf_symlink_project_root_before_writes(self) -> None:
        alias = Path(self.temporary.name) / "project-alias"
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        os.symlink(self.project, alias)
        target_before = tree_fingerprint(self.project)
        alias_target = os.readlink(alias)

        result = self.helper("migrate", "--project-root", str(alias), "--cutover", "--cleanup")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", json.loads(result.stderr)["message"])
        self.assertEqual(tree_fingerprint(self.project), target_before)
        self.assertTrue(alias.is_symlink())
        self.assertEqual(os.readlink(alias), alias_target)
        self.assertEqual(list(outside.iterdir()), [])

    def test_helper_rejects_ancestor_symlink_project_root_before_writes(self) -> None:
        alias_parent = Path(self.temporary.name) / "ancestor-alias"
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        os.symlink(Path(self.temporary.name), alias_parent)
        target_before = tree_fingerprint(self.project)
        alias_target = os.readlink(alias_parent)

        result = self.helper("migrate", "--project-root", str(alias_parent / "project"), "--cutover", "--cleanup")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", json.loads(result.stderr)["message"])
        self.assertEqual(tree_fingerprint(self.project), target_before)
        self.assertTrue(alias_parent.is_symlink())
        self.assertEqual(os.readlink(alias_parent), alias_target)
        self.assertEqual(list(outside.iterdir()), [])

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
        candidate_index_path = self.project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/index.json"
        candidate_index = json.loads(candidate_index_path.read_text(encoding="utf-8"))
        self.assertEqual(candidate_index["schema_version"], 2)
        self.assertTrue(candidate_index["active_cases"])
        self.assertNotEqual(candidate_index["migration"]["candidate_digest"], "0" * 64)
        self.assertFalse((self.project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/current.md").exists())
        coverage_path = self.project / f".teamwork/runtime/migrations/{migration_id}/coverage.json"
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        baseline_paths = {row["path"] for row in approved_request["baseline"]["paths"]}
        self.assertEqual(set(coverage["baseline_paths"]), baseline_paths)
        self.assertEqual(
            {row["source_path"] for row in coverage["coverage_rows"] if not row.get("derived_terminal_result")},
            baseline_paths,
        )
        legacy_case = next(row for row in candidate_index["active_cases"] if row["task_key"] == "legacy")
        expected_seed = CONTRACT["case_digest"](
            "legacy-migration-case-seed",
            {
                "migration_id": migration_id,
                "group_key": "legacy",
                "sources": [
                    {
                        "path": "docs/teamwork/current.md",
                        "sha256": next(row["sha256"] for row in approved_request["baseline"]["paths"] if row["path"] == "docs/teamwork/current.md"),
                    }
                ],
            },
        )
        self.assertEqual(legacy_case["case_id"], CONTRACT["case_id_from_seed"](expected_seed))
        manifest = json.loads(self.candidate_path(migration_id, legacy_case["manifest_path"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "executing")
        source = next(row for row in manifest["migration_sources"] if row["source_path"] == "docs/teamwork/current.md")
        artifact_row = next(row for row in coverage["coverage_rows"] if row["source_path"] == "docs/teamwork/current.md")
        artifact_text = self.candidate_path(migration_id, artifact_row["artifact_path"]).read_text(encoding="utf-8")
        envelope = {
            "role": manifest["artifacts"][artifact_row["artifact_id"]]["role"],
            "subtype": manifest["artifacts"][artifact_row["artifact_id"]]["subtype"],
            "case_id": legacy_case["case_id"],
            "claim_ids": [],
            "consumer": "teamwork-migration",
            "source_revision": source["source_digest"],
            "immutable": True,
        }
        self.assertEqual(artifact_row["artifact_id"], CONTRACT["artifact_id_for_case"]("result", envelope, artifact_text))
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

    def test_cutover_recovers_from_prepared_journal_without_tamper(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        cutover_request = CONTRACT["migration_phase_request"](
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
            json.dumps(cutover_request),
            env={"TEAMWORK_MIGRATION_FAILPOINT": "after-cutover-prepared"},
        )
        self.assertNotEqual(interrupted.returncode, 0)
        journal_path = self.project / f".teamwork/runtime/migrations/{migration_id}/cutover-journal.json"
        self.assertEqual(json.loads(journal_path.read_text(encoding="utf-8"))["phase"], "prepared")
        self.assertEqual(json.loads((self.memory / "index.json").read_text(encoding="utf-8"))["schema_version"], 1)

        recovered = self.apply(cutover_request)
        self.assertEqual(recovered["phase"], "committed")
        self.assertEqual(json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))["schema_version"], 2)
        self.assertTrue((self.project / recovered["renamed_old_tree"]).is_dir())

    def test_cutover_recovery_rejects_tampered_journal_paths_without_rename(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        cutover_request = CONTRACT["migration_phase_request"](
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
            json.dumps(cutover_request),
            env={"TEAMWORK_MIGRATION_FAILPOINT": "after-cutover-prepared"},
        )
        self.assertNotEqual(interrupted.returncode, 0)

        journal_path = self.project / f".teamwork/runtime/migrations/{migration_id}/cutover-journal.json"
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        journal["renamed_old_tree"] = f".teamwork/runtime/migrations/{migration_id}/renamed-old/tampered-docs-teamwork"
        journal_path.write_text(json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        old_index = (self.project / "docs/teamwork/index.json").read_bytes()

        recovered = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(cutover_request),
        )
        self.assertNotEqual(recovered.returncode, 0)
        payload = json.loads(recovered.stderr)
        self.assertEqual(payload["category"], "INDETERMINATE")
        self.assertIn("cutover journal renamed_old_tree", payload["message"])
        self.assertEqual((self.project / "docs/teamwork/index.json").read_bytes(), old_index)
        self.assertFalse((self.project / f".teamwork/runtime/migrations/{migration_id}/renamed-old/docs-teamwork").exists())
        self.assertFalse((self.project / f".teamwork/runtime/migrations/{migration_id}/renamed-old/tampered-docs-teamwork").exists())

    def test_helper_resume_can_cleanup_after_committed_case_v2_cutover(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        self.apply(
            CONTRACT["migration_phase_request"](
                "cutover",
                migration_id,
                baseline_digest,
                cutover_authority="I authorize Teamwork memory cutover",
            )
        )
        self.assertEqual(json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))["schema_version"], 2)
        result = self.helper("resume", "--project-root", str(self.project), "--migration-id", migration_id, "--cleanup")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["phase"], "cleanup_complete")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["cleanup"], "complete")

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

    def test_helper_migrate_resumes_idempotently_without_cutover(self) -> None:
        first = self.helper("migrate", "--project-root", str(self.project))
        self.assertEqual(first.returncode, 0, first.stderr)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["phase"], "candidate_validated")
        migration_id = payload["migration_id"]
        coverage_path = self.project / f".teamwork/runtime/migrations/{migration_id}/coverage.json"
        self.assertTrue(coverage_path.is_file())
        before = coverage_path.read_bytes()

        second = self.helper("migrate", "--project-root", str(self.project))
        self.assertEqual(second.returncode, 0, second.stderr)
        resumed = json.loads(second.stdout)
        self.assertEqual(resumed["migration_id"], migration_id)
        self.assertEqual(resumed["phase"], "candidate_validated")
        self.assertEqual(before, coverage_path.read_bytes())

    def test_prepare_candidate_rejects_unmappable_non_utf8_source_before_outputs(self) -> None:
        binary = self.memory / "binary.md"
        binary.write_bytes(b"\xff\xfe\x00")
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        index["entries"].append(
            {
                "topic": "binary",
                "kind": "report",
                "title": "Binary",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": "docs/teamwork/binary.md",
                "updated": "2026-07-30",
                "summary": "Binary",
            }
        )
        (self.memory / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        result = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(self.next_request("prepare-candidate", migration_id, baseline_digest)),
        )
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stderr)
        self.assertEqual(payload["category"], "PREWRITE_SAFE")
        self.assertIn("non-UTF-8", payload["message"])
        self.assertFalse((self.project / f".teamwork/runtime/migrations/{migration_id}/candidate").exists())

    def test_helper_migrate_rejects_unmappable_source_before_runtime_state(self) -> None:
        (self.memory / "unknown.bin").write_bytes(b"\xff\xfeunknown")
        result = self.helper("migrate", "--project-root", str(self.project), "--cutover", "--cleanup")
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stderr)
        self.assertIn("non-UTF-8", payload["message"])
        self.assertFalse((self.project / ".teamwork").exists())

    def test_init_entrypoint_rejects_unmappable_source_before_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            project = Path(directory) / "project"
            memory = project / "docs/teamwork"
            memory.mkdir(parents=True)
            (memory / "index.json").write_text(json.dumps(legacy_index(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (memory / "current.md").write_text("# Current\n", encoding="utf-8")
            (memory / "README.md").write_text("# README\n", encoding="utf-8")
            (memory / "unknown.bin").write_bytes(b"\xff\xfeunknown")
            result = subprocess.run(
                [str(INIT_SH), "--project-root", str(project), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-UTF-8", result.stderr)
            self.assertFalse((project / ".teamwork").exists())

    def test_helper_migrate_rejects_malformed_partial_v2_before_already_success(self) -> None:
        shutil_project = self.project
        for path in sorted((shutil_project / "docs/teamwork").rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        case_id = "c-" + "1" * 64
        malformed = {
            "schema_version": 2,
            "project": {"name": "Malformed", "root": ".", "description": "partial v2"},
            "active_cases": [
                {
                    "case_id": case_id,
                    "manifest_path": f"docs/teamwork/cases/{case_id}/manifest.json",
                    "manifest_revision": "0" * 64,
                    "phase": "executing",
                    "task_key": "partial-v2",
                }
            ],
            "claim_heads": {},
            "aliases": {},
            "recent_cases": [],
            "migration": None,
        }
        self.memory.mkdir(parents=True, exist_ok=True)
        (self.memory / "index.json").write_text(json.dumps(malformed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = self.helper("migrate", "--project-root", str(self.project))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("already-case-v2", result.stdout)
        self.assertFalse((self.project / ".teamwork").exists())

    def test_helper_resume_rejects_malformed_partial_v2_before_already_success(self) -> None:
        shutil_project = self.project
        for path in sorted((shutil_project / "docs/teamwork").rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        case_id = "c-" + "2" * 64
        malformed = {
            "schema_version": 2,
            "project": {"name": "Malformed", "root": ".", "description": "partial v2"},
            "active_cases": [
                {
                    "case_id": case_id,
                    "manifest_path": f"docs/teamwork/cases/{case_id}/manifest.json",
                    "manifest_revision": "0" * 64,
                    "phase": "executing",
                    "task_key": "partial-v2",
                }
            ],
            "claim_heads": {},
            "aliases": {},
            "recent_cases": [],
            "migration": None,
        }
        self.memory.mkdir(parents=True, exist_ok=True)
        (self.memory / "index.json").write_text(json.dumps(malformed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = self.helper("resume", "--project-root", str(self.project), "--migration-id", "m-" + "2" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("already-case-v2", result.stdout)
        self.assertFalse((self.project / ".teamwork").exists())

    def test_allowlisted_auxiliary_binary_is_archived_and_mapped_as_provenance_only(self) -> None:
        reports = self.memory / "reports/state"
        reports.mkdir(parents=True)
        binary = reports / "candidate.index"
        binary_bytes = b"\x81\x00binary-index-preimage"
        binary.write_bytes(binary_bytes)
        os.chmod(binary, 0o640)
        ds_store = self.memory / ".DS_Store"
        ds_store_bytes = b"\x00DS-store-bytes"
        ds_store.write_bytes(ds_store_bytes)
        os.chmod(ds_store, 0o600)

        preflight = self.helper("candidate-preflight", "--project-root", str(self.project))
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        preflight_payload = json.loads(preflight.stdout)
        self.assertTrue(preflight_payload["ok"])
        self.assertEqual(
            {row["path"] for row in preflight_payload["recognized_archive_only_binary"]},
            {"docs/teamwork/.DS_Store", "docs/teamwork/reports/state/candidate.index"},
        )

        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        archive_manifest = json.loads((self.project / f".teamwork/cold-archive/v1/manifests/{migration_id}.json").read_text(encoding="utf-8"))
        objects = {row["source_path"]: row for row in archive_manifest["objects"]}
        for source_path, expected_bytes, expected_mode in (
            ("docs/teamwork/.DS_Store", ds_store_bytes, 0o600),
            ("docs/teamwork/reports/state/candidate.index", binary_bytes, 0o640),
        ):
            with self.subTest(source_path=source_path):
                row = objects[source_path]
                object_path = self.project / row["object_path"]
                self.assertEqual(object_path.read_bytes(), expected_bytes)
                self.assertEqual(row["mode"], expected_mode)
                self.assertEqual(row["size"], len(expected_bytes))
                self.assertEqual(object_path.stat().st_mode & 0o777, 0o444)

        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        coverage = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/coverage.json").read_text(encoding="utf-8"))
        binary_rows = [
            row for row in coverage["coverage_rows"]
            if row["source_path"] in {"docs/teamwork/.DS_Store", "docs/teamwork/reports/state/candidate.index"}
            and not row.get("derived_terminal_result")
        ]
        self.assertEqual(len(binary_rows), 2)
        candidate_index = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/index.json").read_text(encoding="utf-8"))
        self.assertFalse(candidate_index["claim_heads"])
        for row in binary_rows:
            with self.subTest(coverage=row["source_path"]):
                self.assertEqual(row["classification"], "archive-only-binary")
                artifact_text = self.candidate_path(migration_id, row["artifact_path"]).read_text(encoding="utf-8")
                self.assertIn("Archived Binary Source", artifact_text)
                self.assertIn(row["source_path"], artifact_text)
                self.assertIn(row["source_digest"], artifact_text)
                self.assertNotIn("Preserved Text", artifact_text)
                self.assertNotIn("\x00", artifact_text)
                manifest = json.loads(self.candidate_path(migration_id, f"docs/teamwork/cases/{row['case_id']}/manifest.json").read_text(encoding="utf-8"))
                source = next(item for item in manifest["migration_sources"] if item["source_path"] == row["source_path"])
                self.assertEqual(source["classification"], "archive-only-binary")
                self.assertEqual(source["artifact_id"], row["artifact_id"])
                self.assertEqual(manifest["artifacts"][row["artifact_id"]]["path"], row["artifact_path"])
                self.assertEqual(manifest["artifacts"][row["artifact_id"]]["role"], "evidence")

    def test_init_project_entrypoint_migrates_exact_legacy_root_to_v2(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            project = Path(directory) / "project"
            memory = project / "docs/teamwork"
            memory.mkdir(parents=True)
            (memory / "index.json").write_text(json.dumps(legacy_index(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (memory / "current.md").write_text("# Current\n", encoding="utf-8")
            (memory / "README.md").write_text("# README\n", encoding="utf-8")
            result = subprocess.run(
                [str(INIT_SH), "--project-root", str(project), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            index = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["schema_version"], 2)
            self.assertEqual(index["migration"]["phase"], "cleanup_complete")
            self.assertFalse((project / "docs/teamwork/current.md").exists())
            self.assertFalse((project / "docs/teamwork/README.md").exists())
            journal_paths = list((project / ".teamwork/runtime/migrations").glob("m-*/journal.json"))
            self.assertEqual(len(journal_paths), 1)
            journal = json.loads(journal_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(journal["cleanup"], "complete")

    def test_current_repository_read_only_preflight_accepts_recognized_auxiliary_binaries(self) -> None:
        request_inputs = self.helper("request-inputs", "--project-root", str(ROOT))
        self.assertEqual(request_inputs.returncode, 0, request_inputs.stderr)
        request_payload = json.loads(request_inputs.stdout)
        if request_payload["classification"]["mode"] == "case-v2":
            validation = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_teamwork_index.py"), str(ROOT / "docs/teamwork/index.json")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)
            return
        self.assertEqual(request_payload["classification"]["mode"], "legacy-v1")
        self.assertEqual(len(request_payload["baseline"]["paths"]), 227)
        approve = self.cli(
            "migration-request",
            "--project-root",
            str(ROOT),
            "--request-json",
            json.dumps({"schema_version": 1, "operation": "approve-baseline", "migration_seed": "55" * 32}),
        )
        self.assertEqual(approve.returncode, 0, approve.stderr)
        approve_payload = json.loads(approve.stdout)
        self.assertEqual(len(approve_payload["baseline"]["paths"]), 227)
        self.assertEqual(approve_payload["baseline_digest"], request_payload["baseline"]["baseline_digest"])
        preflight = self.helper("candidate-preflight", "--project-root", str(ROOT))
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        payload = json.loads(preflight.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["blocking"], [])
        self.assertLessEqual(payload["shape"]["active_cases"], 32)
        self.assertLessEqual(payload["shape"]["recent_cases"], 10)
        self.assertEqual(payload["shape"]["groups"], 184)
        self.assertEqual(payload["shape"]["manifests"], 184)
        self.assertEqual(payload["shape"]["active_cases"], 6)
        self.assertEqual(payload["shape"]["recent_cases"], 10)
        self.assertEqual(payload["shape"]["aliases"], 16)
        recognized_paths = {row["path"] for row in payload["recognized_archive_only_binary"]}
        self.assertIn("docs/teamwork/.DS_Store", recognized_paths)
        self.assertTrue(any(path.endswith("/candidate.index") for path in recognized_paths))
        self.assertTrue(any(path.endswith("/real-index.preimage") for path in recognized_paths))

    def test_many_group_candidate_filters_aliases_to_hot_cases_and_preserves_manifests(self) -> None:
        for path in sorted(self.memory.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        self.memory.mkdir(parents=True, exist_ok=True)
        active_specs = [
            ("current", "docs/teamwork/current.md", "active-current", "result", "active", "current", "active-summary", {}),
            ("design", "docs/teamwork/design/2026-07-30-active-design.md", "active-design", "design", "accepted", "current", "canonical", {}),
            ("plan", "docs/teamwork/plans/2026-07-30-active-plan.md", "active-plan", "plan", "active", "current", "active-summary", {}),
            ("progress", "docs/teamwork/reports/2026-07-30-active-progress-goal.md", "active-progress", "progress", "active", "current", "active-summary", {}),
            ("report", "docs/teamwork/workflows/review/active-report.md", "active-report", "report", "active", "current", "active-summary", {}),
            ("collaborate", "docs/teamwork/collaborate/current.md", "active-collaborate", "decision", "accepted", "current", "canonical", {"artifact_type": "collaborate"}),
        ]
        active = {key: None for key in ("current", "design", "plan", "progress", "report", "collaborate")}
        active["results"] = []
        entries: list[dict[str, object]] = []
        for slot, path, topic, kind, status, currentness, authority, extra in active_specs:
            active[slot] = path
            target = self.project / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# {topic}\n", encoding="utf-8")
            entry = {
                "topic": topic,
                "kind": kind,
                "title": topic.replace("-", " ").title(),
                "status": status,
                "currentness": currentness,
                "authority": authority,
                "path": path,
                "updated": "2026-07-30",
                "summary": topic,
            }
            entry.update(extra)
            entries.append(entry)
        closed_dir = self.memory / "history"
        closed_dir.mkdir(parents=True)
        for index in range(176):
            topic = f"closed-{index:03d}"
            path = f"docs/teamwork/history/{topic}.md"
            (self.project / path).write_text(f"# {topic}\n", encoding="utf-8")
            month = index % 12 + 1
            day = index % 28 + 1
            entries.append(
                {
                    "topic": topic,
                    "kind": "result",
                    "title": topic.replace("-", " ").title(),
                    "status": "accepted",
                    "currentness": "historical",
                    "authority": "historical",
                    "path": path,
                    "updated": f"2026-{month:02d}-{day:02d}",
                    "summary": topic,
                }
            )
        (self.memory / "README.md").write_text("# README\n", encoding="utf-8")
        legacy = {
            "schema_version": 1,
            "last_updated": "2026-07-30",
            "project": {"name": "Many Groups", "root": ".", "description": "legacy"},
            "active": active,
            "entries": entries,
        }
        (self.memory / "index.json").write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        preflight = self.helper("candidate-preflight", "--project-root", str(self.project))
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        payload = json.loads(preflight.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["blocking"], [])
        self.assertEqual(payload["shape"]["groups"], 184)
        self.assertEqual(payload["shape"]["manifests"], 184)
        self.assertEqual(payload["shape"]["active_cases"], 6)
        self.assertEqual(payload["shape"]["recent_cases"], 10)
        self.assertEqual(payload["shape"]["aliases"], 16)

        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        candidate_root = self.project / f".teamwork/runtime/migrations/{migration_id}/candidate"
        candidate_index_path = candidate_root / "docs-teamwork/index.json"
        candidate_index = json.loads(candidate_index_path.read_text(encoding="utf-8"))
        hot_case_ids = {row["case_id"] for row in candidate_index["active_cases"] + candidate_index["recent_cases"]}
        self.assertEqual(set(row["target_id"] for row in candidate_index["aliases"].values()), hot_case_ids)
        self.assertEqual(len(candidate_index["aliases"]), 16)
        manifest_paths = sorted((candidate_root / "docs-teamwork/cases").glob("c-*/manifest.json"))
        self.assertEqual(len(manifest_paths), 184)
        preserved_sources = 0
        accepted_collaborate_artifact = None
        for manifest_path in manifest_paths:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            preserved_sources += len(manifest["migration_sources"])
            for source in manifest["migration_sources"]:
                if source["source_path"] == "docs/teamwork/collaborate/current.md":
                    accepted_collaborate_artifact = manifest["artifacts"][source["artifact_id"]]
        self.assertEqual(preserved_sources, 184)
        self.assertIsNotNone(accepted_collaborate_artifact)
        self.assertEqual(accepted_collaborate_artifact["role"], "decision")
        self.assertTrue(accepted_collaborate_artifact["path"].endswith("/decision.md"))
        with tempfile.TemporaryDirectory(dir=ROOT) as validation_directory:
            validation_root = Path(validation_directory)
            shutil.copytree(candidate_root / "docs-teamwork", validation_root / "docs/teamwork")
            validation = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_teamwork_index.py"), str(validation_root / "docs/teamwork/index.json")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)

    def test_active_results_imports_artifact_without_active_phase_vote(self) -> None:
        result_path = "docs/teamwork/workflows/review/2026-07-30-retrieval-only.md"
        review_dir = self.memory / "workflows/review"
        review_dir.mkdir(parents=True)
        (self.project / result_path).write_text("# Retrieval only\n", encoding="utf-8")
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        index["active"]["results"] = [result_path]
        index["entries"].append(
            {
                "topic": "retrieval-only",
                "kind": "report",
                "title": "Retrieval Only",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": result_path,
                "updated": "2026-07-30",
                "summary": "Active results is retrieval history only.",
            }
        )
        (self.memory / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        candidate_index = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/index.json").read_text(encoding="utf-8"))
        self.assertFalse(any(row["task_key"] == "retrieval-only" for row in candidate_index["active_cases"]))
        self.assertTrue(any(row["case_id"] for row in candidate_index["recent_cases"]))

    def test_active_goal_progress_migrates_live_goal_with_claim_head(self) -> None:
        goal_path = "docs/teamwork/reports/2026-07-30-repository-goal-goal.md"
        (self.memory / "reports").mkdir(parents=True, exist_ok=True)
        (self.project / goal_path).write_text("# Repository Goal\n\nKeep working until done.\n", encoding="utf-8")
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        index["active"]["progress"] = goal_path
        index["entries"].append(
            {
                "topic": "repository-goal",
                "kind": "progress",
                "title": "Repository Goal",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": goal_path,
                "updated": "2026-07-30",
                "summary": "Active Goal route.",
            }
        )
        (self.memory / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        candidate_index = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/index.json").read_text(encoding="utf-8"))
        case_row = next(row for row in candidate_index["active_cases"] if row["task_key"] == "repository-goal")
        self.assertEqual(case_row["phase"], "executing")
        manifest = json.loads(self.candidate_path(migration_id, case_row["manifest_path"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "executing")
        self.assertTrue(manifest["claims"])
        claim_id, claim = next(iter(manifest["claims"].items()))
        self.assertIn(claim_id, candidate_index["claim_heads"])
        self.assertEqual(candidate_index["claim_heads"][claim_id]["artifact_id"], claim["head_artifact_id"])
        goal_artifact = manifest["artifacts"][claim["head_artifact_id"]]
        self.assertEqual(goal_artifact["role"], "goal")
        self.assertEqual(goal_artifact["path"], f"docs/teamwork/cases/{case_row['case_id']}/live/goal.md")
        self.assertTrue(self.candidate_path(migration_id, goal_artifact["path"]).is_file())

    def test_candidate_tamper_fails_before_installing_legacy_cutover(self) -> None:
        for target in ("artifact", "manifest", "coverage"):
            with self.subTest(target=target):
                with tempfile.TemporaryDirectory() as temporary:
                    project = Path(temporary) / "project"
                    memory = project / "docs/teamwork"
                    memory.mkdir(parents=True)
                    (memory / "index.json").write_text(json.dumps(legacy_index(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    (memory / "current.md").write_text("# Current\n", encoding="utf-8")
                    (memory / "README.md").write_text("# README\n", encoding="utf-8")
                    def run(*args: str) -> subprocess.CompletedProcess[str]:
                        return subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, text=True, capture_output=True, check=False)
                    request = run(
                        "migration-request",
                        "--project-root",
                        str(project),
                        "--request-json",
                        json.dumps({"schema_version": 1, "operation": "approve-baseline", "migration_seed": "44" * 32}),
                    )
                    self.assertEqual(request.returncode, 0, request.stderr)
                    approved_request = json.loads(request.stdout)
                    for payload in (
                        approved_request,
                        CONTRACT["migration_phase_request"]("materialize-archive", approved_request["migration_id"], approved_request["baseline_digest"]),
                        CONTRACT["migration_phase_request"]("prepare-candidate", approved_request["migration_id"], approved_request["baseline_digest"]),
                        CONTRACT["migration_phase_request"]("restore-drill", approved_request["migration_id"], approved_request["baseline_digest"]),
                    ):
                        applied = run("migration-apply", "--project-root", str(project), "--request-json", json.dumps(payload))
                        self.assertEqual(applied.returncode, 0, applied.stderr)
                    migration_id = approved_request["migration_id"]
                    candidate_index = json.loads((project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/index.json").read_text(encoding="utf-8"))
                    if target == "coverage":
                        tamper_path = project / f".teamwork/runtime/migrations/{migration_id}/coverage.json"
                    else:
                        manifest_path = candidate_index["active_cases"][0]["manifest_path"]
                        tamper_path = project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/{manifest_path.removeprefix('docs/teamwork/')}"
                        if target == "artifact":
                            manifest = json.loads(tamper_path.read_text(encoding="utf-8"))
                            artifact_path = next(iter(manifest["artifacts"].values()))["path"]
                            tamper_path = project / f".teamwork/runtime/migrations/{migration_id}/candidate/docs-teamwork/{artifact_path.removeprefix('docs/teamwork/')}"
                    tamper_path.write_text(tamper_path.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
                    cutover = run(
                        "migration-apply",
                        "--project-root",
                        str(project),
                        "--request-json",
                        json.dumps(
                            CONTRACT["migration_phase_request"](
                                "cutover",
                                migration_id,
                                approved_request["baseline_digest"],
                                cutover_authority="I authorize Teamwork memory cutover",
                            )
                        ),
                    )
                    self.assertNotEqual(cutover.returncode, 0)
                    self.assertEqual(json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))["schema_version"], 1)

    def test_helper_recovers_after_new_tree_installed_failpoint_and_cleans_up(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        failed = self.helper("resume", "--project-root", str(self.project), "--migration-id", migration_id, "--cutover", "--cleanup", env={"TEAMWORK_MIGRATION_FAILPOINT": "after-new-tree-installed"})
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(json.loads(failed.stderr)["message"].startswith("simulated migration failpoint"), True)
        self.assertEqual(json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))["schema_version"], 2)
        recovered = self.helper("migrate", "--project-root", str(self.project), "--cutover", "--cleanup")
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        payload = json.loads(recovered.stdout)
        self.assertEqual(payload["mode"], "case-v2")
        self.assertEqual(payload["phase"], "cleanup_complete")
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["migration"]["phase"], "cleanup_complete")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["cleanup"], "complete")

    def test_helper_finishes_committed_cleanup_pending_case_v2(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        cutover = self.helper("resume", "--project-root", str(self.project), "--migration-id", migration_id, "--cutover")
        self.assertEqual(cutover.returncode, 0, cutover.stderr)
        self.assertEqual(json.loads(cutover.stdout)["phase"], "committed")
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["schema_version"], 2)
        self.assertEqual(installed["migration"]["phase"], "committed")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["cleanup"], "pending")

        completed = self.helper("migrate", "--project-root", str(self.project), "--cutover", "--cleanup")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        completed_payload = json.loads(completed.stdout)
        self.assertEqual(completed_payload["mode"], "case-v2")
        self.assertEqual(completed_payload["phase"], "cleanup_complete")
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["migration"]["phase"], "cleanup_complete")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["cleanup"], "complete")

    def test_resume_cleanup_fails_if_terminal_readback_is_hybrid_without_further_mutation(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        completed = self.helper("resume", "--project-root", str(self.project), "--migration-id", migration_id, "--cutover", "--cleanup")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["phase"], "cleanup_complete")

        index_path = self.project / "docs/teamwork/index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["last_updated"] = "2026-07-30"
        index["active"] = {"current": "docs/teamwork/current.md", "design": None, "plan": None, "progress": None, "report": None, "results": [], "collaborate": None}
        index["entries"] = []
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        before = tree_fingerprint(self.project)

        failed = self.helper("resume", "--project-root", str(self.project), "--migration-id", migration_id, "--cleanup")

        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("case-v2", json.loads(failed.stderr)["message"])
        self.assertEqual(tree_fingerprint(self.project), before)
        self.assertEqual(list(outside.iterdir()), [])

    def test_helper_recovers_after_installed_index_replaced_before_journal_commit(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        failed = self.helper(
            "resume",
            "--project-root",
            str(self.project),
            "--migration-id",
            migration_id,
            "--cutover",
            "--cleanup",
            env={"TEAMWORK_MIGRATION_FAILPOINT": "after-installed-index-validated-before-journal"},
        )
        self.assertNotEqual(failed.returncode, 0)
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["migration"]["phase"], "committed")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["phase"], "candidate_validated")

        recovered = self.helper("migrate", "--project-root", str(self.project), "--cutover", "--cleanup")
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        recovered_payload = json.loads(recovered.stdout)
        self.assertEqual(recovered_payload["mode"], "case-v2")
        self.assertEqual(recovered_payload["phase"], "cleanup_complete")
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["migration"]["phase"], "cleanup_complete")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["cleanup"], "complete")

    def test_recovery_after_new_tree_installed_tamper_fails_indeterminate_without_commit(self) -> None:
        approved_request = self.request("approve-baseline")
        self.apply(approved_request)
        migration_id = approved_request["migration_id"]
        baseline_digest = approved_request["baseline_digest"]
        self.apply(self.next_request("materialize-archive", migration_id, baseline_digest))
        self.apply(self.next_request("prepare-candidate", migration_id, baseline_digest))
        self.apply(self.next_request("restore-drill", migration_id, baseline_digest))
        cutover_request = CONTRACT["migration_phase_request"](
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
            json.dumps(cutover_request),
            env={"TEAMWORK_MIGRATION_FAILPOINT": "after-new-tree-installed"},
        )
        self.assertNotEqual(interrupted.returncode, 0)
        installed = json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        manifest_path = installed["active_cases"][0]["manifest_path"]
        manifest = json.loads((self.project / manifest_path).read_text(encoding="utf-8"))
        artifact_path = next(iter(manifest["artifacts"].values()))["path"]
        with open(self.project / artifact_path, "a", encoding="utf-8") as handle:
            handle.write("\ntampered after rename\n")
        recovered = self.cli(
            "migration-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(cutover_request),
        )
        self.assertNotEqual(recovered.returncode, 0)
        self.assertEqual(json.loads(recovered.stderr)["category"], "INDETERMINATE")
        journal = json.loads((self.project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["phase"], "candidate_validated")
        self.assertNotEqual(json.loads((self.project / "docs/teamwork/index.json").read_text(encoding="utf-8"))["migration"]["phase"], "committed")

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
        result = self.cli(
            "case-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(
                {
                    "schema_version": 2,
                    "operation": "create",
                    "expected_revision": "0" * 64,
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
