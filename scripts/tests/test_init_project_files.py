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

    def write_legacy_v1_project(self, project: Path) -> None:
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True)
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

    def test_fresh_project_init_is_project_only_and_transaction_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)

            result = self.run_init(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CodeGraph: skipped (explicit consent not given)", result.stdout)
            memory = project / "docs/teamwork"
            self.assertTrue((memory / "index.json").is_file())
            for name in ("current.md", "README.md"):
                self.assertFalse((memory / name).exists(), name)
            for name in ("research", "design", "collaborate", "plans", "reports", "workflows", "discussion"):
                self.assertFalse((memory / name).exists(), name)
            self.assertFalse((project / ".teamwork-init-transaction.json").exists())
            self.assertFalse((memory / ".teamwork-init-transaction.json").exists())
            index = json.loads((memory / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["schema_version"], 2)
            self.assertEqual(index["active_cases"], [])
            self.assertEqual(index["claim_heads"], {})
            self.assertEqual(index["aliases"], {})
            self.assertEqual(index["recent_cases"], [])
            self.assertIsNone(index["migration"])
            agents_text = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(
                "Read `docs/teamwork/index.json` first",
                agents_text,
            )
            self.assertIn(
                "selected v2 case manifest",
                agents_text,
            )
            self.assertIn(
                "live/collaborate.md",
                agents_text,
            )
            self.assertIn("case-inspect", agents_text)
            self.assertNotIn("docs/teamwork/collaborate/current.md", agents_text)
            self.assertNotIn("collaborate-inspect", agents_text)
            self.assertNotIn(
                "sustained Discuss",
                agents_text,
            )
            ignored_text = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("docs/teamwork/**", ignored_text)
            self.assertIn(".teamwork/runtime/**", ignored_text)
            self.assertIn(".teamwork/cold-archive/**", ignored_text)
            self.assertEqual(self.run_files(project, "validate").returncode, 0)

    def test_collaborate_route_selection_is_schema_specific(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fresh = self.project(temporary)
            self.initialize(fresh, label="Fresh")
            fresh_agents = (fresh / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Read `docs/teamwork/index.json` first", fresh_agents)
            self.assertIn("selected v2 case manifest", fresh_agents)
            self.assertIn("live/collaborate.md", fresh_agents)
            self.assertIn("case-inspect", fresh_agents)
            self.assertNotIn("docs/teamwork/collaborate/current.md", fresh_agents)
            self.assertNotIn("collaborate-inspect", fresh_agents)

            legacy = Path(temporary).resolve() / "legacy"
            legacy.mkdir()
            self.write_legacy_v1_project(legacy)
            result = self.run_files(
                legacy,
                "write-context",
                "--today",
                "2026-07-19",
                "--project-label",
                "Legacy",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            legacy_agents = (legacy / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Read `docs/teamwork/index.json` first", legacy_agents)
            self.assertIn("legacy-v1 alone uses `docs/teamwork/collaborate/current.md`", legacy_agents)
            self.assertIn("collaborate-inspect", legacy_agents)
            self.assertNotIn("selected v2 case manifest", legacy_agents)

        skill = (ROOT / "skills/teamwork-collaborate/SKILL.md").read_text(encoding="utf-8")
        v2_segment = skill.split("In case-v2", 1)[1].split("Read-only helpers", 1)[0]
        self.assertIn("case-inspect", v2_segment)
        self.assertIn("live/collaborate.md", skill)
        self.assertNotIn("docs/teamwork/collaborate/current.md", v2_segment)
        self.assertNotIn("collaborate-inspect", v2_segment)
        legacy_segment = skill.split("If legacy-v1, Writer uses:", 1)[1].split("In case-v2", 1)[0]
        self.assertIn("collaborate-inspect", legacy_segment)
        self.assertIn("collaborate-apply", legacy_segment)

        writer = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "templates/codex-agents/teamwork-writer.toml",
                "templates/cursor-agents/writer.md",
                "templates/claude-agents/writer.md",
            )
        )
        self.assertIn("run case-inspect first", writer)
        self.assertIn("v2 case bundle sinks", writer)
        self.assertIn("legacy-v1=`collaborate-inspect", writer)

    def test_repository_project_block_matches_observed_schema(self) -> None:
        index = json.loads((ROOT / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        block = agents.split("<!-- TEAMWORK_PROJECT_START -->", 1)[1].split(
            "<!-- TEAMWORK_PROJECT_END -->", 1
        )[0]
        self.assertIn("Read `docs/teamwork/index.json` first", block)
        if index["schema_version"] == 1:
            self.assertIn("legacy-v1 alone uses `docs/teamwork/collaborate/current.md`", block)
            self.assertIn("collaborate-inspect", block)
            self.assertNotIn("selected v2 case manifest", block)
        elif index["schema_version"] == 2:
            self.assertIn("selected v2 case manifest", block)
            self.assertIn("case-inspect", block)
            self.assertNotIn("docs/teamwork/collaborate/current.md", block)
        else:
            self.fail(f"unsupported schema_version: {index['schema_version']!r}")

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

    def test_teamwork_memory_runtime_and_cold_archive_sinks_are_git_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            result = self.run_files(
                project,
                "write-context",
                "--today",
                "2026-07-30",
                "--project-label",
                "Fixture",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            subprocess.run(["git", "init"], cwd=project, text=True, capture_output=True, check=True)
            checked = subprocess.run(
                [
                    "git",
                    "check-ignore",
                    "docs/teamwork/index.json",
                    "docs/teamwork/cases/c-" + "a" * 64 + "/manifest.json",
                    ".teamwork/runtime/migration/request.json",
                    ".teamwork/cold-archive/v1/objects/sha256/aa/" + "b" * 64,
                ],
                cwd=project,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(
                checked.stdout.splitlines(),
                [
                    "docs/teamwork/index.json",
                    "docs/teamwork/cases/c-" + "a" * 64 + "/manifest.json",
                    ".teamwork/runtime/migration/request.json",
                    ".teamwork/cold-archive/v1/objects/sha256/aa/" + "b" * 64,
                ],
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
