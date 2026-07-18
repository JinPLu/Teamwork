#!/usr/bin/env python3
"""Compatibility coverage for the public install.sh CLI."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
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

    def test_help_exposes_global_routes_and_init_project_only(self) -> None:
        result = self.run_install("--help")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("codex|cursor|claude|all|init-project|plugin-codex-bootstrap", output)
        self.assertIn(
            "`--project-root` is valid only with `init-project` or `plugin-init-project`.",
            output,
        )
        self.assertNotIn("project-codex-agents", output)
        self.assertNotRegex(output, r"(?m)^\s+project\s+")

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

    def test_removed_project_routes_fail_without_local_package_writes(self) -> None:
        project = self.base / "project"
        project.mkdir()
        for target in ("project", "project-codex-agents"):
            with self.subTest(target=target):
                result = self.run_install("--project-root", str(project), target)
                output = result.stdout.decode()
                self.assertEqual(result.returncode, 2, output)
                self.assertIn("Project-local install targets were removed", output)
        for path in (
            project / ".agents",
            project / ".codex" / "agents",
            project / ".cursor" / "skills",
            project / ".claude" / "skills",
        ):
            self.assertFalse(path.exists(), path)

    def test_project_root_is_rejected_outside_init_project(self) -> None:
        project = self.base / "project-root-only"
        project.mkdir()
        result = self.run_install("--project-root", str(project), "codex")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 2, output)
        self.assertIn(
            "--project-root is valid only with the init-project or plugin-init-project target.",
            output,
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
        for profile, expected_lines in expectations.items():
            home = self.base / f"home-{profile}"
            result = self.run_install(
                "--profile",
                profile,
                "--no-codex-routing",
                "codex-agents",
                home=home,
            )
            self.assertEqual(result.returncode, 0, result.stdout.decode())
            worker = (
                home / ".codex" / "agents" / "teamwork-worker.toml"
            ).read_text()
            for expected in expected_lines:
                self.assertIn(expected, worker)

    def test_user_copy_installs_keep_policy_destinations(self) -> None:
        home = self.base / "user-home"
        result = self.run_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        codex_policy = (home / ".codex" / "AGENTS.md").read_text()
        self.assertIn("<!-- TEAMWORK_CODEX_GLOBAL_START -->", codex_policy)
        self.assertTrue((home / ".agents" / "skills" / "teamwork-plan").is_dir())
        self.assertFalse((home / ".codex" / "skills" / "teamwork-plan").exists())
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
