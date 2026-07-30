from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FILES = ROOT / "scripts/init-project-files.py"
INIT = ROOT / "scripts/init-project.sh"
TRANSACTION = ROOT / "scripts/discussion-transaction.py"

ACTIVE_DISCUSSION_PATH = "docs/teamwork/discussion/2026-07-15-output-wording.md"
CLOSED_DISCUSSION_PATH = "docs/teamwork/discussion/2026-07-14-prior-wording.md"


class InitProjectIntegrationTests(unittest.TestCase):
    @staticmethod
    def run_files(project: Path, action: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(FILES), "--project-root", str(project), action, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def initialize(self, project: Path) -> None:
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True, exist_ok=True)
        index = {
            "schema_version": 1,
            "last_updated": "2026-07-19",
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
                    "updated": "2026-07-19",
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
        (memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        (memory / "current.md").write_text(
            "# Teamwork Current State\n\nLast Updated: 2026-07-19\n\n## Active Snapshot\n\n- Current focus: Fixture.\n",
            encoding="utf-8",
        )
        (memory / "README.md").write_text(
            "# Teamwork Runtime Index README\n\nLegacy schema v1 fixture.\n",
            encoding="utf-8",
        )
        self.assertEqual(self.run_files(project, "validate").returncode, 0)

    @staticmethod
    def run_transaction(project: Path, action: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TRANSACTION), action, "--project-root", str(project)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def run_init(project: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(INIT),
                "--project-root",
                str(project),
                "--no-codegraph",
                "--no-cursor-mcp",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def migration_coverage(project: Path) -> dict[str, tuple[dict[str, object], dict[str, object], dict[str, object]]]:
        coverage: dict[str, tuple[dict[str, object], dict[str, object], dict[str, object]]] = {}
        for manifest_path in sorted((project / "docs/teamwork/cases").glob("c-*/manifest.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for source in manifest["migration_sources"]:
                coverage[source["source_path"]] = (
                    manifest,
                    source,
                    manifest["artifacts"][source["artifact_id"]],
                )
        return coverage

    @staticmethod
    def plan_artifact(title: str, updated: str = "2026-07-19") -> str:
        return f"Artifact Type: plan\nLast Updated: {updated}\n\n# {title}\n"

    @staticmethod
    def plan_entry(
        path: str,
        title: str,
        *,
        topic: str,
        status: str = "accepted",
        currentness: str = "current",
        authority: str = "active-summary",
        updated: str = "2026-07-19",
    ) -> dict[str, object]:
        return {
            "topic": topic,
            "kind": "plan",
            "title": title,
            "status": status,
            "currentness": currentness,
            "authority": authority,
            "path": path,
            "updated": updated,
            "summary": f"Plan fixture for {title}.",
        }

    def install_legacy_plan_candidates(
        self,
        project: Path,
        *,
        active_plan: object,
        entries: list[dict[str, object]],
        artifacts: dict[str, str] | None = None,
    ) -> Path:
        index_path = project / "docs/teamwork/index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["active"]["plan"] = active_plan
        index["entries"].extend(entries)
        index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        for path, text in (artifacts or {}).items():
            artifact = project / path
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(text, encoding="utf-8")
        return index_path

    @staticmethod
    def project_state(project: Path) -> dict[str, tuple[object, ...]]:
        result: dict[str, tuple[object, ...]] = {}
        for path in sorted((project, *project.rglob("*")), key=lambda item: item.as_posix()):
            info = path.lstat()
            relative = "." if path == project else path.relative_to(project).as_posix()
            if stat.S_ISREG(info.st_mode):
                result[relative] = (
                    "file",
                    stat.S_IMODE(info.st_mode),
                    info.st_ino,
                    info.st_mtime_ns,
                    path.read_bytes(),
                )
            elif stat.S_ISDIR(info.st_mode):
                result[relative] = ("directory", stat.S_IMODE(info.st_mode), info.st_ino)
            elif stat.S_ISLNK(info.st_mode):
                result[relative] = ("symlink", os.readlink(path))
            else:
                result[relative] = ("other", info.st_mode)
        return result

    @staticmethod
    def legacy_discussion() -> str:
        return """Artifact Type: discussion
Status: active
Authority: supporting
Last Updated: 2026-07-15
Search Keys: output wording, evidence order
Abstract: Tracks the remaining evidence-order decision.
Linked Artifacts: none
Superseded By: none

# Researcher-facing output wording

## Goal

Keep replies concise and decision-relevant.

## Settled

- Use plain wording.

## Still open

- Which evidence should lead the reply?

## Key evidence

- The audience rubric rejects internal process inventory.

## Decision map

```mermaid
flowchart LR
    Old["Legacy route"]
```

## Continue here

Choose the evidence that should lead the next reply.
"""

    def test_init_is_project_local_even_with_legacy_install_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)

            result = subprocess.run(
                [
                    str(INIT),
                    "--project-root",
                    str(project),
                    "--copy",
                    "--profile",
                    "performance-first",
                    "--project-only",
                    "--no-cursor-policy-copy",
                    "--no-codegraph",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / "docs/teamwork/index.json").is_file())
            self.assertEqual(list(home.iterdir()), [])
            self.assertNotIn("Global Teamwork", result.stdout + result.stderr)
            self.assertNotIn("Cursor User Rules", result.stdout + result.stderr)

    def test_codegraph_requires_explicit_consent_and_runs_before_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            project = base / "project"
            bin_dir = base / "bin"
            project.mkdir()
            bin_dir.mkdir()
            fake = bin_dir / "codegraph"
            fake.write_text(
                "#!/bin/sh\n"
                "mkdir .codegraph\n"
                "pwd > .codegraph/cwd.txt\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

            skipped = subprocess.run(
                [str(INIT), "--project-root", str(project)],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(skipped.returncode, 0, skipped.stderr)
            self.assertFalse((project / ".codegraph").exists())

            consented = subprocess.run(
                [str(INIT), "--project-root", str(project), "--codegraph"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(consented.returncode, 0, consented.stderr)
            self.assertEqual(
                (project / ".codegraph/cwd.txt").read_text(encoding="utf-8").strip(),
                str(project),
            )
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("local `.codegraph/` index", agents)

    def test_codegraph_failure_is_nonfatal_after_explicit_consent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            project = base / "project"
            bin_dir = base / "bin"
            project.mkdir()
            bin_dir.mkdir()
            fake = bin_dir / "codegraph"
            fake.write_text("#!/bin/sh\nexit 23\n", encoding="utf-8")
            fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

            result = subprocess.run(
                [str(INIT), "--project-root", str(project), "--codegraph"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CodeGraph: init failed", result.stderr)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / "docs/teamwork/index.json").is_file())

    def test_null_legacy_discussion_key_migrates_through_exact_root_init_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            self.initialize(project)
            index_path = project / "docs/teamwork/index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["active"]["discussion"] = None
            index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

            migrated = self.run_init(project)

            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            migrated_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertEqual(migrated_index["schema_version"], 2)
            self.assertEqual(migrated_index["migration"]["phase"], "cleanup_complete")
            inspected = self.run_transaction(project, "case-inspect")
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            self.assertEqual(json.loads(inspected.stdout)["schema_mode"], "case-v2")

            before_repeat = (
                index_path.read_bytes(),
                index_path.stat().st_ino,
                index_path.stat().st_mtime_ns,
            )
            repeated = self.run_init(project)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(
                (
                    index_path.read_bytes(),
                    index_path.stat().st_ino,
                    index_path.stat().st_mtime_ns,
                ),
                before_repeat,
            )

    def test_active_and_historical_plans_migrate_to_case_v2_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            self.initialize(project)
            selected = "docs/teamwork/plans/2026-07-19-selected.md"
            prior = "docs/teamwork/plans/2026-07-18-prior.md"
            already_historical = "docs/teamwork/plans/2026-07-17-historical.md"
            selected_entry = self.plan_entry(selected, "Selected plan", topic="selected")
            prior_entry = self.plan_entry(prior, "Prior plan", topic="prior")
            historical_entry = self.plan_entry(
                already_historical,
                "Historical plan",
                topic="historical",
                status="historical",
                currentness="historical",
                authority="historical",
                updated="2026-07-17",
            )
            index_path = self.install_legacy_plan_candidates(
                project,
                active_plan=selected,
                entries=[selected_entry, prior_entry, historical_entry],
                artifacts={
                    selected: self.plan_artifact("Selected plan"),
                    prior: self.plan_artifact("Prior plan", "2026-07-18"),
                    already_historical: self.plan_artifact("Historical plan", "2026-07-17"),
                },
            )

            migrated = self.run_init(project)

            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            coverage = self.migration_coverage(project)
            self.assertTrue({selected, prior, already_historical}.issubset(coverage))
            selected_manifest, _, selected_artifact = coverage[selected]
            self.assertEqual(selected_manifest["status"], "planned")
            self.assertEqual(selected_artifact["role"], "plan")
            self.assertEqual(coverage[prior][2]["role"], "plan")
            self.assertEqual(coverage[already_historical][2]["role"], "plan")

            before_repeat = (
                index_path.read_bytes(),
                index_path.stat().st_ino,
                index_path.stat().st_mtime_ns,
            )
            repeated = self.run_init(project)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(
                (
                    index_path.read_bytes(),
                    index_path.stat().st_ino,
                    index_path.stat().st_mtime_ns,
                ),
                before_repeat,
            )

    def test_invalid_active_plan_states_fail_before_journal_or_mutation(self) -> None:
        selected = "docs/teamwork/plans/2026-07-19-selected.md"
        other = "docs/teamwork/plans/2026-07-18-other.md"
        eligible = self.plan_entry(selected, "Selected plan", topic="selected")
        cases = {
            "null-with-eligible": (
                None,
                [eligible],
                {selected: self.plan_artifact("Selected plan")},
                "active.plan is null",
            ),
            "malformed-pointer": (
                "docs/teamwork/plans/../selected.md",
                [eligible],
                {selected: self.plan_artifact("Selected plan")},
                "active.plan must be a normalized path",
            ),
            "missing-row": (
                other,
                [eligible],
                {selected: self.plan_artifact("Selected plan")},
                "active.plan has no eligible ordinary-memory entry",
            ),
            "duplicate-row": (
                selected,
                [eligible, dict(eligible)],
                {selected: self.plan_artifact("Selected plan")},
                "exactly one index row",
            ),
            "ineligible-target": (
                selected,
                [dict(eligible, currentness="historical")],
                {selected: self.plan_artifact("Selected plan")},
                "active.plan has no eligible ordinary-memory entry",
            ),
            "missing-artifact": (
                selected,
                [eligible],
                {},
                "cannot inspect active.plan parent",
            ),
            "artifact-disagrees": (
                selected,
                [eligible],
                {selected: self.plan_artifact("Different title")},
                "active.plan artifact does not agree",
            ),
        }
        for name, (pointer, entries, artifacts, message) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary).resolve() / "project"
                project.mkdir()
                self.initialize(project)
                self.install_legacy_plan_candidates(
                    project,
                    active_plan=pointer,
                    entries=entries,
                    artifacts=artifacts,
                )
                before = self.project_state(project)

                result = self.run_files(
                    project,
                    "write-context",
                    "--today",
                    "2026-07-19",
                    "--project-label",
                    "Fixture",
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual(self.project_state(project), before)
                self.assertFalse((project / ".teamwork-init-transaction.json").exists())
                self.assertFalse(
                    (project / "docs/teamwork/.teamwork-init-transaction.json").exists()
                )

    def test_init_semantically_migrates_legacy_discussion_and_cold_archives_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            self.initialize(project)
            memory = project / "docs/teamwork"
            discussion = memory / "discussion"
            discussion.mkdir()
            artifact = project / ACTIVE_DISCUSSION_PATH
            source = self.legacy_discussion()
            artifact.write_text(source, encoding="utf-8")
            closed_artifact = project / CLOSED_DISCUSSION_PATH
            closed_source = self.legacy_discussion().replace(
                "# Researcher-facing output wording", "# Prior output wording"
            )
            closed_artifact.write_text(closed_source, encoding="utf-8")
            index_path = memory / "index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["active"]["discussion"] = ACTIVE_DISCUSSION_PATH
            index["entries"].append(
                {
                    "topic": "output-wording",
                    "kind": "discussion",
                    "title": "Researcher-facing output wording",
                    "status": "active",
                    "currentness": "current",
                    "authority": "supporting",
                    "path": ACTIVE_DISCUSSION_PATH,
                    "applies_to": ["docs/teamwork/discussion/"],
                    "linked": [],
                    "evidence_paths": [ACTIVE_DISCUSSION_PATH],
                    "supersedes": [],
                    "search_keys": ["output wording", "evidence order"],
                    "updated": "2026-07-15",
                    "summary": "Tracks the active output wording decision.",
                }
            )
            index["entries"].append(
                {
                    "topic": "prior-output-wording",
                    "kind": "discussion",
                    "title": "Prior output wording",
                    "status": "accepted",
                    "currentness": "historical",
                    "authority": "historical",
                    "path": CLOSED_DISCUSSION_PATH,
                    "applies_to": ["docs/teamwork/discussion/"],
                    "linked": [],
                    "evidence_paths": [CLOSED_DISCUSSION_PATH],
                    "supersedes": [],
                    "search_keys": ["prior output wording"],
                    "updated": "2026-07-14",
                    "summary": "Preserves an accepted historical wording decision.",
                }
            )
            index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
            current_path = memory / "current.md"
            current_path.write_text(
                current_path.read_text(encoding="utf-8")
                + f"\n- Active discussion: {ACTIVE_DISCUSSION_PATH}.\n",
                encoding="utf-8",
            )
            readme_path = memory / "README.md"
            readme_path.write_text(
                readme_path.read_text(encoding="utf-8")
                + f"\n- Active discussion route: {ACTIVE_DISCUSSION_PATH}\n",
                encoding="utf-8",
            )

            migrated = self.run_init(project)

            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            self.assertFalse(artifact.exists())
            self.assertFalse(closed_artifact.exists())
            migrated_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertEqual(migrated_index["schema_version"], 2)
            self.assertEqual(migrated_index["migration"]["phase"], "cleanup_complete")
            coverage = self.migration_coverage(project)
            self.assertTrue({ACTIVE_DISCUSSION_PATH, CLOSED_DISCUSSION_PATH}.issubset(coverage))
            self.assertEqual(coverage[ACTIVE_DISCUSSION_PATH][2]["role"], "evidence")
            self.assertEqual(coverage[CLOSED_DISCUSSION_PATH][2]["role"], "evidence")
            archive_manifests = sorted((project / ".teamwork/cold-archive/v1/manifests").glob("m-*.json"))
            self.assertEqual(len(archive_manifests), 1)
            archive = json.loads(archive_manifests[0].read_text(encoding="utf-8"))
            archived_paths = {row["source_path"] for row in archive["objects"]}
            self.assertIn(ACTIVE_DISCUSSION_PATH, archived_paths)
            self.assertIn(CLOSED_DISCUSSION_PATH, archived_paths)
            index_bytes = index_path.read_bytes()
            index_identity = (index_path.stat().st_ino, index_path.stat().st_mtime_ns)
            repeated = self.run_init(project)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(index_path.read_bytes(), index_bytes)
            self.assertEqual((index_path.stat().st_ino, index_path.stat().st_mtime_ns), index_identity)

    def test_symlinked_project_root_component_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            real = base / "real"
            real.mkdir()
            linked = base / "linked"
            linked.symlink_to(real, target_is_directory=True)

            result = subprocess.run(
                [str(INIT), "--project-root", str(linked), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlinked project-root component", result.stderr)
            self.assertEqual(list(real.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
