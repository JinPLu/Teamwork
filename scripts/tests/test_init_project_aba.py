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
ACTIVE_DISCUSSION_PATH = "docs/teamwork/discussion/2026-07-15-output-wording.md"


class InitProjectAbaTests(unittest.TestCase):
    @staticmethod
    def state(root: Path) -> dict[str, tuple[object, ...]]:
        result: dict[str, tuple[object, ...]] = {}
        for path in sorted((root, *root.rglob("*")), key=lambda item: item.as_posix()):
            info = path.lstat()
            relative = "." if path == root else path.relative_to(root).as_posix()
            if stat.S_ISREG(info.st_mode):
                result[relative] = (
                    "file",
                    info.st_mode,
                    info.st_dev,
                    info.st_ino,
                    info.st_mtime_ns,
                    path.read_bytes(),
                )
            elif stat.S_ISDIR(info.st_mode):
                result[relative] = ("directory", info.st_mode, info.st_dev, info.st_ino)
            else:
                result[relative] = ("other", info.st_mode)
        return result

    @staticmethod
    def run_files(project: Path, action: str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            [sys.executable, str(FILES), "--project-root", str(project), action, *args],
            cwd=ROOT,
            env=run_env,
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
    def legacy_discussion() -> str:
        return """Artifact Type: discussion
Status: active
Authority: supporting
Last Updated: 2026-07-15

# Researcher-facing output wording

## Goal

Keep replies concise and decision-relevant.

## Settled

- Use plain wording.

## Still open

- Which evidence should lead the reply?

## Key evidence

- The audience rubric rejects internal process inventory.

## Continue here

Choose the evidence that should lead the next reply.
"""

    def install_legacy_active_discussion(self, project: Path) -> None:
        memory = project / "docs/teamwork"
        discussion = memory / "discussion"
        discussion.mkdir()
        (project / ACTIVE_DISCUSSION_PATH).write_text(self.legacy_discussion(), encoding="utf-8")
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
        index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def install_legacy_plan_candidates(project: Path) -> None:
        selected = "docs/teamwork/plans/2026-07-19-selected.md"
        prior = "docs/teamwork/plans/2026-07-18-prior.md"
        plans = project / "docs/teamwork/plans"
        plans.mkdir(exist_ok=True)
        (project / selected).write_text(
            "Artifact Type: plan\nLast Updated: 2026-07-19\n\n# Selected plan\n",
            encoding="utf-8",
        )
        (project / prior).write_text(
            "Artifact Type: plan\nLast Updated: 2026-07-18\n\n# Prior plan\n",
            encoding="utf-8",
        )
        index_path = project / "docs/teamwork/index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["active"]["plan"] = selected
        for path, title, topic, updated in (
            (selected, "Selected plan", "selected", "2026-07-19"),
            (prior, "Prior plan", "prior", "2026-07-18"),
        ):
            index["entries"].append(
                {
                    "topic": topic,
                    "kind": "plan",
                    "title": title,
                    "status": "accepted",
                    "currentness": "current",
                    "authority": "active-summary",
                    "path": path,
                    "updated": updated,
                    "summary": f"Plan fixture for {title}.",
                }
            )
        index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    def test_hard_interruption_recovers_the_exact_empty_prestate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            before = self.state(project)

            interrupted = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                env={"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "1"},
            )

            self.assertEqual(interrupted.returncode, 86, interrupted.stderr)
            self.assertTrue((project / ".teamwork-init-transaction.json").is_file())
            recovered = self.run_files(project, "preflight")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertEqual(self.state(project), before)
            self.assertFalse((project / ".teamwork-init-transaction.json").exists())

    def test_each_journal_phase_recovers_or_finishes_durably(self) -> None:
        rollback_phases = {"preparing", "prepared", "committing"}
        for phase in ("preparing", "prepared", "committing", "committed", "cleanup"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary).resolve() / "project"
                project.mkdir()
                before = self.state(project)

                interrupted = self.run_files(
                    project,
                    "write-context",
                    "--today",
                    "2026-07-19",
                    env={"TEAMWORK_TEST_HARD_EXIT_INIT_PHASE": phase},
                )

                self.assertEqual(interrupted.returncode, 86, interrupted.stderr)
                recovered = self.run_files(project, "preflight")
                self.assertEqual(recovered.returncode, 0, recovered.stderr)
                self.assertFalse((project / ".teamwork-init-transaction.json").exists())
                if phase in rollback_phases:
                    self.assertEqual(self.state(project), before)
                else:
                    self.assertEqual(self.run_files(project, "validate").returncode, 0)

    def test_aba_change_preserves_the_external_replacement_and_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            self.initialize(project)
            ignored = project / ".gitignore"
            ignored.write_text(
                ignored.read_text(encoding="utf-8").replace(".codegraph/\n", ""),
                encoding="utf-8",
            )

            interrupted = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Changed",
                env={"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "1"},
            )

            self.assertEqual(interrupted.returncode, 86, interrupted.stderr)
            agents = project / "AGENTS.md"
            agents.write_text("external writer wins\n", encoding="utf-8")
            recovered = self.run_files(project, "preflight")

            self.assertNotEqual(recovered.returncode, 0)
            self.assertIn("changed externally", recovered.stderr)
            self.assertEqual(agents.read_text(encoding="utf-8"), "external writer wins\n")
            self.assertTrue((project / ".teamwork-init-transaction.json").is_file())

    def test_w4_delete_recovers_exact_prestate_or_finishes_when_committed(self) -> None:
        for case in ("after-delete", "committed"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary).resolve() / "project"
                project.mkdir()
                self.initialize(project)
                self.install_legacy_active_discussion(project)
                before = self.state(project)
                env = (
                    {"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "2"}
                    if case == "after-delete"
                    else {"TEAMWORK_TEST_HARD_EXIT_INIT_PHASE": "committed"}
                )

                interrupted = self.run_files(
                    project,
                    "write-context",
                    "--today",
                    "2026-07-19",
                    "--project-label",
                    "Fixture",
                    env=env,
                )

                self.assertEqual(interrupted.returncode, 86, interrupted.stderr)
                recovered = self.run_files(project, "preflight")
                self.assertEqual(recovered.returncode, 0, recovered.stderr)
                old_artifact = project / ACTIVE_DISCUSSION_PATH
                current_artifact = project / "docs/teamwork/discussion/current.md"
                if case == "after-delete":
                    self.assertEqual(self.state(project), before)
                    self.assertTrue(old_artifact.is_file())
                    self.assertFalse(current_artifact.exists())
                else:
                    self.assertFalse(old_artifact.exists())
                    self.assertTrue(current_artifact.is_file())
                    self.assertEqual(self.run_files(project, "validate").returncode, 0)

    def test_plan_currentness_repair_recovers_exact_prestate_after_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            self.initialize(project)
            self.install_legacy_plan_candidates(project)
            before = self.state(project)

            interrupted = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
                env={"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "1"},
            )

            self.assertEqual(interrupted.returncode, 86, interrupted.stderr)
            self.assertTrue((project / ".teamwork-init-transaction.json").is_file())
            recovered = self.run_files(project, "preflight")
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertEqual(self.state(project), before)
            self.assertFalse((project / ".teamwork-init-transaction.json").exists())

    def test_root_journal_recovers_when_the_docs_mirror_lags_one_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            self.initialize(project)
            ignored = project / ".gitignore"
            ignored.write_text(
                ignored.read_text(encoding="utf-8").replace(".codegraph/\n", ""),
                encoding="utf-8",
            )
            before = self.state(project)

            interrupted = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Changed",
                env={"TEAMWORK_TEST_HARD_EXIT_INIT_PHASE": "prepared"},
            )

            self.assertEqual(interrupted.returncode, 86, interrupted.stderr)
            root_marker = project / ".teamwork-init-transaction.json"
            mirror_marker = project / "docs/teamwork/.teamwork-init-transaction.json"
            root_journal = json.loads(root_marker.read_text(encoding="utf-8"))
            self.assertEqual(root_journal["phase"], "prepared")
            self.assertEqual(root_journal, json.loads(mirror_marker.read_text(encoding="utf-8")))
            # This is the durable state after root's atomic marker replacement
            # succeeds and the process exits before replacing the mirror.
            root_journal["phase"] = "committing"
            root_marker.write_text(
                json.dumps(root_journal, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )

            recovered = self.run_files(project, "preflight")

            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertEqual(self.state(project), before)
            self.assertFalse(root_marker.exists())
            self.assertFalse(mirror_marker.exists())


if __name__ == "__main__":
    unittest.main()
