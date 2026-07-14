#!/usr/bin/env python3
"""Compatibility coverage for the public install.sh CLI."""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HELP_SHA256 = "c58162666d237d3dee4c746b81fcbf347071c3b09d8da008c86eb12162e799e2"


class InstallCliCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tempdir.name)
        self.fixture = self.base / "fixture"
        self.fixture.mkdir()
        shutil.copy2(REPO_ROOT / "install.sh", self.fixture / "install.sh")
        shutil.copy2(REPO_ROOT / "VERSION", self.fixture / "VERSION")
        (self.fixture / "scripts").mkdir()
        shutil.copytree(
            REPO_ROOT / "scripts" / "install",
            self.fixture / "scripts" / "install",
        )
        os.symlink(REPO_ROOT / "skills", self.fixture / "skills")
        os.symlink(REPO_ROOT / "templates", self.fixture / "templates")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_install(
        self, *args: str, home: pathlib.Path | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        env = os.environ.copy()
        env.pop("TEAMWORK_INSTALL_MODE", None)
        env.pop("TEAMWORK_CODEX_PROFILE", None)
        env.pop("TEAMWORK_NOTIFICATIONS_ACTION", None)
        env.pop("TEAMWORK_CODEX_ROUTING", None)
        env["HOME"] = str(home or (self.base / "home"))
        pathlib.Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
        return subprocess.run(
            ["bash", str(self.fixture / "install.sh"), *args],
            cwd=self.fixture,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_help_output_contract(self) -> None:
        result = self.run_install("--help")
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), HELP_SHA256)

    def test_invalid_arguments_keep_exit_and_usage_contract(self) -> None:
        result = self.run_install("--not-a-real-option")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 2, output)
        self.assertTrue(output.startswith("Unknown argument: --not-a-real-option\n"))
        self.assertIn("Usage:\n  ./install.sh", output)

        result = self.run_install("codex", "cursor")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 2, output)
        self.assertTrue(output.startswith("Specify only one install target.\n"))

    def test_project_copy_and_link_destinations(self) -> None:
        copy_root = self.base / "copy-project"
        link_root = self.base / "link-project"
        copy_root.mkdir()
        link_root.mkdir()

        result = self.run_install("--project-root", str(copy_root), "project")
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        copied_skill = copy_root / ".agents" / "skills" / "using-teamwork"
        copied_agent = copy_root / ".codex" / "agents" / "teamwork-worker.toml"
        self.assertTrue(copied_skill.is_dir())
        self.assertFalse(copied_skill.is_symlink())
        self.assertTrue(copied_agent.is_file())
        self.assertFalse(copied_agent.is_symlink())

        result = self.run_install(
            "--link", "--project-root", str(link_root), "project"
        )
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        self.assertTrue(
            (link_root / ".agents" / "skills" / "using-teamwork").is_symlink()
        )
        self.assertTrue(
            (link_root / ".codex" / "agents" / "teamwork-worker.toml").is_symlink()
        )

    def test_profile_aliases_render_expected_codex_models(self) -> None:
        expectations = {
            "performance-first": ('model = "gpt-5.6-sol"', 'model_reasoning_effort = "medium"'),
            "gpt56-role": ('model = "gpt-5.6-sol"', 'model_reasoning_effort = "medium"'),
            "cost-first": ('model = "gpt-5.6-terra"', 'model_reasoning_effort = "medium"'),
            "gpt56-high": ('model = "gpt-5.6-sol"', 'model_reasoning_effort = "high"'),
            "gpt55-high": ('model = "gpt-5.6-sol"', 'model_reasoning_effort = "high"'),
            "gpt56-xhigh": ('model = "gpt-5.6-sol"', 'model_reasoning_effort = "xhigh"'),
            "gpt55-xhigh": ('model = "gpt-5.6-sol"', 'model_reasoning_effort = "xhigh"'),
        }
        project_root = self.base / "profiles"
        project_root.mkdir()
        for profile, expected_lines in expectations.items():
            result = self.run_install(
                "--profile",
                profile,
                "--project-root",
                str(project_root),
                "project-codex-agents",
            )
            self.assertEqual(result.returncode, 0, result.stdout.decode())
            worker = (
                project_root / ".codex" / "agents" / "teamwork-worker.toml"
            ).read_text()
            for expected in expected_lines:
                self.assertIn(expected, worker)

    def test_user_copy_installs_keep_policy_destinations(self) -> None:
        home = self.base / "user-home"
        result = self.run_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        codex_policy = (home / ".codex" / "AGENTS.md").read_text()
        self.assertIn("<!-- TEAMWORK_CODEX_GLOBAL_START -->", codex_policy)
        self.assertTrue((home / ".codex" / "skills" / "teamwork-plan").is_dir())
        self.assertTrue(
            (home / ".codex" / "agents" / "teamwork-reviewer.toml").is_file()
        )

        result = self.run_install("claude", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        claude_policy = (home / ".claude" / "CLAUDE.md").read_text()
        self.assertIn("<!-- TEAMWORK_CLAUDE_GLOBAL_START -->", claude_policy)
        self.assertTrue((home / ".claude" / "agents" / "worker.md").is_file())


if __name__ == "__main__":
    unittest.main()
