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
        result = self.run_files(
            project,
            "write-context",
            "--today",
            "2026-07-19",
            "--project-label",
            "Fixture",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

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

    def test_present_null_legacy_discussion_key_is_removed_idempotently_and_unlocks_design(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            self.initialize(project)
            index_path = project / "docs/teamwork/index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            expected_active = dict(index["active"])
            index["active"]["discussion"] = None
            index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

            pending = self.run_files(project, "validate")
            self.assertNotEqual(pending.returncode, 0)
            self.assertIn("ordinary-memory anchor repair is pending", pending.stderr)

            migrated = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
            )

            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            migrated_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertNotIn("discussion", migrated_index["active"])
            self.assertEqual(migrated_index["active"], expected_active)
            artifact_check = self.run_transaction(project, "artifact-index-validate")
            self.assertEqual(artifact_check.returncode, 0, artifact_check.stderr)
            design = self.run_transaction(project, "design-inspect")
            self.assertEqual(design.returncode, 0, design.stderr)
            design_state = json.loads(design.stdout)
            self.assertTrue(design_state["initialized"])
            self.assertIsNone(design_state["active"])
            self.assertRegex(design_state["revision"], r"^[0-9a-f]{64}$")

            before_repeat = (
                index_path.read_bytes(),
                index_path.stat().st_ino,
                index_path.stat().st_mtime_ns,
            )
            repeated = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
            )
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(
                (
                    index_path.read_bytes(),
                    index_path.stat().st_ino,
                    index_path.stat().st_mtime_ns,
                ),
                before_repeat,
            )

    def test_active_plan_selects_one_candidate_and_only_demotes_other_eligible_plans(self) -> None:
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

            migrated = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
            )

            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            repaired = json.loads(index_path.read_text(encoding="utf-8"))
            by_path = {entry["path"]: entry for entry in repaired["entries"]}
            self.assertEqual(by_path[selected], selected_entry)
            expected_prior = dict(prior_entry)
            expected_prior["currentness"] = "historical"
            self.assertEqual(by_path[prior], expected_prior)
            self.assertEqual(by_path[already_historical], historical_entry)
            validated = self.run_transaction(project, "artifact-index-validate")
            self.assertEqual(validated.returncode, 0, validated.stderr)

            before_repeat = (
                index_path.read_bytes(),
                index_path.stat().st_ino,
                index_path.stat().st_mtime_ns,
            )
            repeated = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
            )
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
                "missing or unreadable active.plan",
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

    def test_init_uses_the_w4_migration_plan_and_repairs_anchors_atomically(self) -> None:
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

            migrated = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
            )

            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            current_artifact = memory / "discussion/current.md"
            self.assertFalse(artifact.exists())
            self.assertTrue(current_artifact.is_file())
            migrated_text = current_artifact.read_text(encoding="utf-8")
            self.assertIn('"migration_source"', migrated_text)
            self.assertIn(ACTIVE_DISCUSSION_PATH, migrated_text)
            closed_text = closed_artifact.read_text(encoding="utf-8")
            self.assertIn("Status: accepted", closed_text)
            self.assertIn(CLOSED_DISCUSSION_PATH, closed_text)
            self.assertIn("- Active discussion: none.", (memory / "current.md").read_text(encoding="utf-8"))
            self.assertIn("- Active discussion route: none", (memory / "README.md").read_text(encoding="utf-8"))
            migrated_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertNotIn("discussion", migrated_index["active"])
            self.assertFalse(any(entry.get("kind") == "discussion" for entry in migrated_index["entries"]))
            self.assertEqual(self.run_files(project, "validate").returncode, 0)
            index_bytes = index_path.read_bytes()
            index_identity = (index_path.stat().st_ino, index_path.stat().st_mtime_ns)
            repeated = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
            )
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(current_artifact.read_text(encoding="utf-8"), migrated_text)
            self.assertEqual(closed_artifact.read_text(encoding="utf-8"), closed_text)
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
