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


class InitProjectFilesTests(unittest.TestCase):
    def project(self, temporary: str) -> Path:
        project = Path(temporary).resolve() / "project"
        project.mkdir()
        return project

    def run_files(
        self,
        project: Path,
        action: str,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
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

    def run_init(self, project: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(INIT), "--project-root", str(project), "--no-codegraph", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def tree_state(root: Path) -> dict[str, tuple[object, ...]]:
        state: dict[str, tuple[object, ...]] = {}
        for path in sorted((root, *root.rglob("*")), key=lambda item: item.as_posix()):
            info = path.lstat()
            relative = "." if path == root else path.relative_to(root).as_posix()
            if stat.S_ISREG(info.st_mode):
                state[relative] = (
                    "file",
                    info.st_mode,
                    info.st_dev,
                    info.st_ino,
                    info.st_mtime_ns,
                    path.read_bytes(),
                )
            elif stat.S_ISDIR(info.st_mode):
                state[relative] = ("directory", info.st_mode, info.st_dev, info.st_ino)
            elif stat.S_ISLNK(info.st_mode):
                state[relative] = ("symlink", info.st_mode, os.readlink(path))
            else:
                state[relative] = ("other", info.st_mode)
        return state

    def initialize(self, project: Path, *, label: str = "Fixture") -> None:
        result = self.run_files(
            project,
            "write-context",
            "--today",
            "2026-07-19",
            "--project-label",
            label,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fresh_project_init_is_project_only_and_transaction_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)

            result = self.run_init(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CodeGraph: skipped (explicit consent not given)", result.stdout)
            memory = project / "docs/teamwork"
            for name in ("index.json", "current.md", "README.md"):
                self.assertTrue((memory / name).is_file(), name)
            for name in ("research", "design", "plans", "reports", "workflows"):
                self.assertTrue((memory / name).is_dir(), name)
            self.assertFalse((memory / "discussion").exists())
            self.assertFalse((project / ".teamwork-init-transaction.json").exists())
            self.assertFalse((memory / ".teamwork-init-transaction.json").exists())
            index = json.loads((memory / "index.json").read_text(encoding="utf-8"))
            self.assertNotIn("discussion", index["active"])
            self.assertNotIn(
                "docs/teamwork/discussion",
                (memory / "README.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(self.run_files(project, "validate").returncode, 0)

    def test_no_change_preserves_bytes_identity_mtime_and_has_no_temps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            self.initialize(project)
            before = self.tree_state(project)

            result = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Fixture",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.tree_state(project), before)
            self.assertEqual(
                [path for path in project.rglob("*.teamwork-init-*")],
                [],
            )

    def test_duplicate_managed_block_fails_before_any_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            self.initialize(project)
            agents = project / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8")
                + "\n<!-- TEAMWORK_PROJECT_START -->\n## Teamwork Project Instructions\n<!-- TEAMWORK_PROJECT_END -->\n",
                encoding="utf-8",
            )
            before = self.tree_state(project)

            result = self.run_files(project, "write-context", "--today", "2026-07-19")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("managed block markers are ambiguous", result.stderr)
            self.assertEqual(self.tree_state(project), before)

    def test_w4_discussion_transaction_markers_block_init_without_mutation(self) -> None:
        for relative in (
            "docs/teamwork/discussion/.discussion-transaction.json",
            "docs/teamwork/.discussion-transaction.json",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                self.initialize(project)
                marker = project / relative
                marker.parent.mkdir(exist_ok=True)
                marker.write_text("{}\n", encoding="utf-8")
                before = self.tree_state(project)

                result = self.run_files(project, "write-context", "--today", "2026-07-19")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("unfinished W4 discussion transaction", result.stderr)
                self.assertEqual(self.tree_state(project), before)

    def test_controlled_replace_failure_restores_all_bytes_and_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            self.initialize(project)
            ignored = project / ".gitignore"
            ignored.write_text(
                ignored.read_text(encoding="utf-8").replace(".codegraph/\n", ""),
                encoding="utf-8",
            )
            before = self.tree_state(project)

            result = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Changed",
                env={"TEAMWORK_TEST_FAIL_INIT_REPLACE_AT": "2"},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exact prestate was restored", result.stderr)
            self.assertEqual(self.tree_state(project), before)
            self.assertFalse((project / ".teamwork-init-transaction.json").exists())

    def test_symlinked_root_output_is_rejected_before_directory_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            project = base / "project"
            project.mkdir()
            outside = base / "outside"
            outside.write_text("untouched\n", encoding="utf-8")
            (project / "AGENTS.md").symlink_to(outside)

            result = self.run_files(project, "write-context", "--today", "2026-07-19")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("single-link same-device regular file", result.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), "untouched\n")
            self.assertFalse((project / "docs").exists())

    def test_unknown_journal_is_retained_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            marker = project / ".teamwork-init-transaction.json"
            marker.write_text("{}\n", encoding="utf-8")
            os.chmod(marker, 0o600)

            result = self.run_files(project, "preflight")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("init journal fields are invalid", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "{}\n")

    def test_full_bootstrap_emits_matrix_only_when_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            regular = self.run_files(project, "write-context", "--today", "2026-07-19")
            self.assertEqual(regular.returncode, 0, regular.stderr)
            self.assertEqual(regular.stdout, "")

            full = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--full-bootstrap",
            )
            self.assertEqual(full.returncode, 0, full.stderr)
            matrix = json.loads(full.stdout)
            self.assertEqual(matrix["mode"], "full-bootstrap")
            self.assertGreater(matrix["published_surface_counts"]["deterministic"], 0)
            self.assertFalse((project / "docs/teamwork/capability-matrix.json").exists())

    def test_candidate_promotion_never_happens_implicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            candidate = Path(temporary) / "candidate.json"
            candidate.write_text("{}\n", encoding="utf-8")

            result = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-19",
                "--candidate-memory",
                str(candidate),
                "--promote-candidates",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("explicit full bootstrap and Root authority", result.stderr)
            self.assertFalse((project / "docs").exists())

    def test_v342_preflight_uses_full_owned_surface_authority_not_skill_subset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)

            result = self.run_files(project, "v342-preflight")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertGreater(report["deterministic_surfaces"], 100)
            self.assertGreater(report["runtime_surfaces"], 1)
            self.assertFalse(report["skill_subset_authoritative"])


if __name__ == "__main__":
    unittest.main()
