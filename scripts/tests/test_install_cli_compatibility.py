#!/usr/bin/env python3
"""Compatibility coverage for the public install.sh CLI."""

from __future__ import annotations

import os
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
V342_SURFACES = REPO_ROOT / "scripts/tests/fixtures/v3.4.2-owned-surfaces.json"
EXPECTED_SKILLS = {
    "grill-me",
    "teamwork-debug",
    "teamwork-design",
    "teamwork-explore",
    "teamwork-goal",
    "teamwork-init",
    "teamwork-plan",
    "teamwork-research",
    "teamwork-review",
    "teamwork-update",
}
EXPECTED_CODEX_AGENTS = {
    "teamwork-researcher.toml",
    "teamwork-explorer.toml",
    "teamwork-debugger.toml",
    "teamwork-designer.toml",
    "teamwork-planner.toml",
    "teamwork-worker.toml",
    "teamwork-plan-reviewer.toml",
    "teamwork-reviewer.toml",
}
CODEX_PROFILE_MATRICES = {
    "performance-first": {
        "teamwork-researcher": ("gpt-5.5", "high"),
        "teamwork-explorer": ("gpt-5.5", "high"),
        "teamwork-debugger": ("gpt-5.5", "high"),
        "teamwork-designer": ("gpt-5.6-sol", "high"),
        "teamwork-planner": ("gpt-5.5", "high"),
        "teamwork-worker": ("gpt-5.5", "high"),
        "teamwork-plan-reviewer": ("gpt-5.6-sol", "high"),
        "teamwork-reviewer": ("gpt-5.6-sol", "max"),
    },
    "cost-first": {
        "teamwork-researcher": ("gpt-5.5", "medium"),
        "teamwork-explorer": ("gpt-5.5", "medium"),
        "teamwork-debugger": ("gpt-5.5", "medium"),
        "teamwork-designer": ("gpt-5.6-sol", "medium"),
        "teamwork-planner": ("gpt-5.5", "medium"),
        "teamwork-worker": ("gpt-5.5", "medium"),
        "teamwork-plan-reviewer": ("gpt-5.6-sol", "high"),
        "teamwork-reviewer": ("gpt-5.6-sol", "high"),
    },
}


class InstallCliCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tempdir.name)
        self.fixture = self.base / "fixture"
        self.fixture.mkdir()
        shutil.copy2(REPO_ROOT / "install.sh", self.fixture / "install.sh")
        shutil.copy2(REPO_ROOT / "VERSION", self.fixture / "VERSION")
        (self.fixture / "scripts").mkdir()
        shutil.copy2(
            REPO_ROOT / "scripts" / "configure-notifications.py",
            self.fixture / "scripts" / "configure-notifications.py",
        )
        shutil.copytree(
            REPO_ROOT / "scripts" / "install",
            self.fixture / "scripts" / "install",
        )
        fixture_root = self.fixture / "scripts" / "tests" / "fixtures"
        fixture_root.mkdir(parents=True)
        shutil.copy2(V342_SURFACES, fixture_root / V342_SURFACES.name)
        shutil.copytree(REPO_ROOT / "hooks", self.fixture / "hooks")
        os.symlink(REPO_ROOT / "skills", self.fixture / "skills")
        os.symlink(REPO_ROOT / "templates", self.fixture / "templates")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_install(
        self,
        *args: str,
        home: pathlib.Path | None = None,
        create_home: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        env = os.environ.copy()
        env.pop("TEAMWORK_INSTALL_MODE", None)
        env.pop("TEAMWORK_CODEX_PROFILE", None)
        env.pop("TEAMWORK_NOTIFICATIONS_ACTION", None)
        env.pop("TEAMWORK_CODEX_ROUTING", None)
        env["HOME"] = str(home or (self.base / "home"))
        if create_home:
            pathlib.Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
        return subprocess.run(
            ["bash", str(self.fixture / "install.sh"), *args],
            cwd=self.fixture,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def install_exact_v342_generic_router(self, home: pathlib.Path) -> pathlib.Path:
        fixture = json.loads(V342_SURFACES.read_text(encoding="utf-8"))
        router = home / ".codex" / "skills" / "teamwork"
        prefix = "skills/using-teamwork/"
        for row in fixture["deterministic_surfaces"]:
            source = row.get("path", "")
            if not source.startswith(prefix):
                continue
            relative = source.removeprefix(prefix)
            result = subprocess.run(
                ["git", "show", f"{fixture['commit']}:{source}"],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            content = result.stdout
            if relative == "SKILL.md":
                content = content.replace(
                    b"name: using-teamwork\n", b"name: teamwork\n", 1
                )
            destination = router / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(int(row["mode"], 8))
        return router

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
        self.assertNotIn("init-project refreshes the user-level routing", output)
        self.assertIn("Project init never changes user-level routing", output)
        self.assertIn("cost-first uses GPT-5.5/medium", output)
        self.assertIn("Worker; Sol/medium for Designer;", output)
        self.assertIn("Sol/high for Plan Reviewer and Reviewer.", output)
        self.assertIn("Cursor and Claude Code keep their existing profile mappings.", output)
        self.assertNotIn("cost-first lowers only", output)

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

    def test_supported_profiles_render_exact_codex_matrix(self) -> None:
        for profile, matrix in CODEX_PROFILE_MATRICES.items():
            home = self.base / f"home-{profile}"
            result = self.run_install(
                "--profile",
                profile,
                "--no-codex-routing",
                "codex-agents",
                home=home,
            )
            self.assertEqual(result.returncode, 0, result.stdout.decode())
            agent_root = home / ".codex" / "agents"
            for agent, (model, effort) in matrix.items():
                with self.subTest(profile=profile, agent=agent):
                    rendered = (agent_root / f"{agent}.toml").read_text()
                    self.assertIn(f'model = "{model}"', rendered)
                    self.assertIn(
                        f'model_reasoning_effort = "{effort}"', rendered
                    )

    def test_removed_profile_alias_fails_closed(self) -> None:
        result = self.run_install("--profile", "gpt56-role", "codex-agents")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 2, output)
        self.assertIn("Unknown profile: gpt56-role", output)

    def test_user_copy_installs_keep_policy_destinations(self) -> None:
        home = self.base / "user-home"
        result = self.run_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        codex_policy = (home / ".codex" / "AGENTS.md").read_text()
        self.assertIn("<!-- TEAMWORK_CODEX_GLOBAL_START -->", codex_policy)
        codex_skills = home / ".agents" / "skills"
        self.assertEqual(
            {path.name for path in codex_skills.iterdir() if path.is_dir()},
            EXPECTED_SKILLS,
        )
        self.assertTrue(
            (codex_skills / "teamwork-debug" / "references" / "runtime-diagnosis.md").is_file()
        )
        self.assertTrue(
            (codex_skills / "teamwork-research" / "references" / "deep-research.md").is_file()
        )
        self.assertTrue(
            (codex_skills / "teamwork-review" / "references" / "strict-review.md").is_file()
        )
        self.assertFalse((codex_skills / "using-teamwork").exists())
        self.assertFalse((codex_skills / "teamwork-execute").exists())
        self.assertFalse((home / ".codex" / "skills" / "teamwork-plan").exists())
        codex_agents = home / ".codex" / "agents"
        self.assertEqual(
            {path.name for path in codex_agents.iterdir() if path.is_file()},
            EXPECTED_CODEX_AGENTS,
        )

        result = self.run_install("claude", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        claude_policy = (home / ".claude" / "CLAUDE.md").read_text()
        self.assertIn("<!-- TEAMWORK_CLAUDE_GLOBAL_START -->", claude_policy)
        self.assertTrue((home / ".claude" / "agents" / "worker.md").is_file())

    def test_all_install_creates_a_missing_home(self) -> None:
        home = self.base / "missing-home"
        result = self.run_install(
            "--profile",
            "cost-first",
            "--no-codex-routing",
            "all",
            home=home,
            create_home=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        self.assertTrue((home / ".codex" / "AGENTS.md").is_file())
        self.assertTrue((home / ".claude" / "CLAUDE.md").is_file())

    def test_owned_skill_content_drift_is_refreshed(self) -> None:
        home = self.base / "drifted-home"
        installed = self.run_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(installed.returncode, 0, installed.stdout.decode())

        skill = home / ".agents" / "skills" / "grill-me" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8") + "\n# stale fixture\n",
            encoding="utf-8",
        )

        refreshed = self.run_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(refreshed.returncode, 0, refreshed.stdout.decode())
        self.assertNotIn("# stale fixture", skill.read_text(encoding="utf-8"))

    def test_unknown_legacy_generic_router_is_preserved(self) -> None:
        home = self.base / "unknown-legacy-router-home"
        legacy = home / ".codex" / "skills" / "teamwork"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text(
            "---\nname: teamwork\ndescription: User-owned legacy skill.\n---\n",
            encoding="utf-8",
        )
        notes = legacy / "notes.md"
        notes.write_text("keep me\n", encoding="utf-8")

        result = self.run_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        self.assertTrue(notes.is_file())
        self.assertTrue((home / ".agents" / "skills" / "grill-me" / "SKILL.md").is_file())

    def test_exact_v342_generic_router_is_removed(self) -> None:
        home = self.base / "exact-legacy-router-home"
        router = self.install_exact_v342_generic_router(home)

        result = self.run_install("--no-codex-routing", "codex", home=home)

        self.assertEqual(result.returncode, 0, result.stdout.decode())
        self.assertFalse(router.exists())

    def test_drifted_v342_generic_router_is_preserved(self) -> None:
        cases = ("content", "type", "mode")
        for case in cases:
            with self.subTest(case=case):
                home = self.base / f"drifted-legacy-router-{case}"
                router = self.install_exact_v342_generic_router(home)
                target = router / "references" / "workflow-contract.md"
                if case == "content":
                    target.write_bytes(target.read_bytes() + b"user change\n")
                elif case == "type":
                    target.unlink()
                    target.symlink_to(router / "SKILL.md")
                else:
                    target.chmod(0o600)

                result = self.run_install(
                    "--no-codex-routing", "codex", home=home
                )

                self.assertEqual(result.returncode, 0, result.stdout.decode())
                self.assertTrue(router.is_dir())
                if case == "content":
                    self.assertTrue(target.read_bytes().endswith(b"user change\n"))
                elif case == "type":
                    self.assertTrue(target.is_symlink())
                else:
                    self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_same_named_unowned_agent_is_preserved_on_all_three_hosts(self) -> None:
        cases = (
            ("codex", ".codex/agents/teamwork-researcher.toml", ("--no-codex-routing", "codex-agents")),
            ("cursor", ".cursor/agents/researcher.md", ("cursor-agents",)),
            ("claude", ".claude/agents/researcher.md", ("claude-agents",)),
        )
        for platform, relative, args in cases:
            with self.subTest(platform=platform):
                home = self.base / f"unowned-agent-{platform}"
                agent = home / relative
                agent.parent.mkdir(parents=True)
                content = f"user-owned {platform} researcher\n".encode()
                agent.write_bytes(content)

                result = self.run_install(*args, home=home)

                self.assertNotEqual(result.returncode, 0, result.stdout.decode())
                self.assertIn(
                    "not a recognized Teamwork-owned profile",
                    result.stdout.decode(),
                )
                self.assertEqual(agent.read_bytes(), content)

    def test_unmarked_skill_is_never_claimed_as_teamwork_owned(self) -> None:
        home = self.base / "legacy-design-home"
        legacy = home / ".cursor" / "skills" / "teamwork-design"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text(
            "---\nname: teamwork-design\ndescription: Use when designing.\n---\n",
            encoding="utf-8",
        )

        result = self.run_install("cursor", home=home)
        self.assertNotEqual(result.returncode, 0, result.stdout.decode())
        self.assertIn("without Teamwork ownership markers", result.stdout.decode())
        self.assertEqual(
            (legacy / "SKILL.md").read_text(encoding="utf-8"),
            "---\nname: teamwork-design\ndescription: Use when designing.\n---\n",
        )


if __name__ == "__main__":
    unittest.main()
