from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "scripts/init-project.sh"


def legacy_index() -> dict[str, object]:
    return {
        "schema_version": 1,
        "last_updated": "2026-07-19",
        "project": {"name": "Fixture", "root": ".", "description": "legacy"},
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
                "topic": "legacy-current",
                "kind": "result",
                "title": "Legacy current",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": "docs/teamwork/current.md",
                "applies_to": ["docs/teamwork/"],
                "linked": [],
                "evidence_paths": ["docs/teamwork/current.md"],
                "supersedes": [],
                "search_keys": ["legacy-current"],
                "updated": "2026-07-19",
                "summary": "Legacy project state.",
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


class InitProjectIntegrationTests(unittest.TestCase):
    def test_cursor_mcp_requires_explicit_consent_and_writes_project_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            project.mkdir()
            result = subprocess.run(
                [str(INIT), "--project-root", str(project), "--no-codegraph", "--cursor-mcp"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / ".cursor/rules/codegraph.mdc").is_file())
            self.assertTrue((project / ".cursor/rules/gpu-broker.mdc").is_file())
            payload = json.loads((project / ".cursor/mcp.json").read_text(encoding="utf-8"))
            self.assertEqual({"codegraph", "gpu-broker"}, set(payload["mcpServers"]))

    def test_cursor_mcp_conflict_fails_before_teamwork_context_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            cursor = project / ".cursor"
            cursor.mkdir(parents=True)
            config = cursor / "mcp.json"
            config.write_text(
                json.dumps({"mcpServers": {"codegraph": {"command": "user-owned"}}}) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [str(INIT), "--project-root", str(project), "--no-codegraph", "--cursor-mcp"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to replace unrecognized Cursor MCP server", result.stderr)
            self.assertFalse((project / "docs/teamwork").exists())
            self.assertFalse((project / "AGENTS.md").exists())

    def test_init_rejects_retired_install_flags_without_writes(self) -> None:
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
                    "--no-codegraph",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("Unknown argument: --copy", result.stderr)
            self.assertFalse((project / "docs/teamwork").exists())
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertEqual(list(home.iterdir()), [])

    def test_codegraph_requires_explicit_consent_and_runs_before_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            skipped_project = base / "skipped-project"
            consented_project = base / "consented-project"
            bin_dir = base / "bin"
            skipped_project.mkdir()
            consented_project.mkdir()
            bin_dir.mkdir()
            fake = bin_dir / "codegraph"
            fake.write_text("#!/bin/sh\nmkdir .codegraph\npwd > .codegraph/cwd.txt\n", encoding="utf-8")
            fake.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

            skipped = subprocess.run(
                [str(INIT), "--project-root", str(skipped_project)],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(skipped.returncode, 0, skipped.stderr)
            self.assertFalse((skipped_project / ".codegraph").exists())

            consented = subprocess.run(
                [str(INIT), "--project-root", str(consented_project), "--codegraph"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(consented.returncode, 0, consented.stderr)
            self.assertEqual(
                (consented_project / ".codegraph/cwd.txt").read_text(encoding="utf-8").strip(),
                str(consented_project),
            )
            self.assertIn(
                "local `.codegraph/` index",
                (consented_project / "AGENTS.md").read_text(encoding="utf-8"),
            )

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

    def test_init_rejects_legacy_memory_and_leaves_it_for_update(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            memory = project / "docs/teamwork"
            memory.mkdir(parents=True)
            index_path = memory / "index.json"
            index_path.write_text(json.dumps(legacy_index(), indent=2) + "\n", encoding="utf-8")
            current = memory / "current.md"
            current.write_text("# Legacy current\n", encoding="utf-8")
            (memory / "README.md").write_text("# Legacy runtime\n", encoding="utf-8")
            before = {path.relative_to(project).as_posix(): path.read_bytes() for path in project.rglob("*") if path.is_file()}

            result = subprocess.run(
                [str(INIT), "--project-root", str(project), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Update", result.stderr)
            after = {path.relative_to(project).as_posix(): path.read_bytes() for path in project.rglob("*") if path.is_file()}
            self.assertEqual(after, before)
            self.assertFalse((project / "AGENTS.md").exists())

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
