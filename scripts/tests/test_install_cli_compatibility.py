#!/usr/bin/env python3
"""Compatibility coverage for the public install.sh CLI."""

from __future__ import annotations

import http.server
import os
import json
import pathlib
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
V342_SURFACES = REPO_ROOT / "scripts/tests/fixtures/v3.4.2-owned-surfaces.json"
RETIRED_V5 = REPO_ROOT / "scripts/tests/fixtures/retired-teamwork-skills-v5.json"
EXPECTED_SKILLS = {
    "teamwork-collaborate",
    "teamwork-debug",
    "teamwork-explore",
    "teamwork-goal",
    "teamwork-init",
    "teamwork-plan",
    "teamwork-research",
    "teamwork-review",
    "teamwork-update",
}
PLATFORM_SKILL_ROOTS = {
    "codex": pathlib.Path(".agents/skills"),
    "cursor": pathlib.Path(".cursor/skills"),
    "claude": pathlib.Path(".claude/skills"),
}
EXPECTED_CODEX_AGENTS = {
    "teamwork-researcher.toml",
    "teamwork-explorer.toml",
    "teamwork-debugger.toml",
    "teamwork-designer.toml",
    "teamwork-planner.toml",
    "teamwork-worker.toml",
    "teamwork-writer.toml",
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
        "teamwork-writer": ("gpt-5.5", "low"),
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
        "teamwork-writer": ("gpt-5.5", "low"),
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
        shutil.copy2(
            REPO_ROOT / "scripts" / "configure-codex-routing.py",
            self.fixture / "scripts" / "configure-codex-routing.py",
        )
        shutil.copy2(
            REPO_ROOT / "scripts" / "codex_routing_config.py",
            self.fixture / "scripts" / "codex_routing_config.py",
        )
        shutil.copytree(
            REPO_ROOT / "scripts" / "install",
            self.fixture / "scripts" / "install",
        )
        fixture_root = self.fixture / "scripts" / "tests" / "fixtures"
        fixture_root.mkdir(parents=True)
        shutil.copy2(V342_SURFACES, fixture_root / V342_SURFACES.name)
        shutil.copy2(RETIRED_V5, fixture_root / RETIRED_V5.name)
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
        env.pop("TEAMWORK_MANAGED_DEPENDENCIES", None)
        env.pop("TEAMWORK_CODEGRAPH_PACKAGE", None)
        env.pop("TEAMWORK_CODEGRAPH_VERSION", None)
        env.pop("TEAMWORK_GPU_BROKER_SOURCE", None)
        env.pop("TEAMWORK_GPU_BROKER_URL", None)
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

    def install_exact_v46_grill(
        self,
        home: pathlib.Path,
        platform: str,
        *,
        ownership_markers: bool = True,
    ) -> pathlib.Path:
        root = home / PLATFORM_SKILL_ROOTS[platform]
        skill = root / "grill-me" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        result = subprocess.run(
            ["git", "show", "v4.6.0:skills/grill-me/SKILL.md"],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        skill.write_bytes(result.stdout)
        if ownership_markers:
            (root / ".teamwork-version").write_text("4.6.0\n", encoding="utf-8")
            (root / ".teamwork-profile").write_text(
                "performance-first\n", encoding="utf-8"
            )
        return skill

    def install_retired_from_fixture(
        self,
        home: pathlib.Path,
        platform: str,
        retired: str,
        manifest_index: int = 0,
    ) -> pathlib.Path:
        fixture = json.loads(RETIRED_V5.read_text(encoding="utf-8"))
        manifest = fixture["skills"][retired][manifest_index]
        root = home / PLATFORM_SKILL_ROOTS[platform]
        skill_root = root / retired
        for row in manifest["files"]:
            source_path = f"{manifest['source_tree']}/{row['path']}"
            result = subprocess.run(
                ["git", "show", f"{manifest['source_commit']}:{source_path}"],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            content = result.stdout
            if manifest.get("projection") == "teamwork-router" and row["path"] == "SKILL.md":
                content = content.replace(
                    b"name: using-teamwork\n", b"name: teamwork\n", 1
                )
            destination = skill_root / row["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(int(row["mode"], 8))
        (root / ".teamwork-version").write_text("4.6.0\n", encoding="utf-8")
        (root / ".teamwork-profile").write_text(
            "performance-first\n", encoding="utf-8"
        )
        return skill_root

    def run_readiness(
        self, home: pathlib.Path
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["CODEX_HOME"] = str(home / ".codex")
        return subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "scripts" / "check-update.sh"),
                "--readiness",
                "--no-fetch",
            ],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    def test_help_exposes_global_routes_and_init_project_only(self) -> None:
        result = self.run_install("--help")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("codex|cursor|claude|all|update|init-project|plugin-codex-bootstrap", output)
        self.assertIn("--dependencies|--no-dependencies", output)
        self.assertIn(
            "`--project-root` is valid only with `init-project` or `plugin-init-project`.",
            output,
        )
        self.assertNotIn("project-codex-agents", output)
        self.assertNotRegex(output, r"(?m)^\s+project\s+")
        self.assertNotIn("init-project refreshes the user-level routing", output)
        self.assertIn("Project init never changes user-level routing", output)
        self.assertIn("cost-first uses GPT-5.5/medium", output)
        self.assertIn("Worker; GPT-5.5/low for Writer; Sol/medium for Designer;", output)
        self.assertIn("Sol/high for Plan Reviewer and Reviewer.", output)
        self.assertIn("Writer is fixed to the simplest model in both profiles.", output)
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
            (codex_skills / "teamwork-collaborate" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (codex_skills / "teamwork-research" / "references" / "deep-research.md").is_file()
        )
        self.assertTrue(
            (codex_skills / "teamwork-review" / "references" / "strict-review.md").is_file()
        )
        self.assertFalse((codex_skills / "using-teamwork").exists())
        self.assertFalse((codex_skills / "teamwork-execute").exists())
        self.assertFalse((codex_skills / "teamwork-design").exists())
        self.assertFalse((codex_skills / "teamwork-discuss").exists())
        self.assertFalse((codex_skills / "grill-me").exists())
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

    def test_update_fails_before_global_writes_without_local_gpu_companion(self) -> None:
        home = self.base / "update-missing-companion"
        result = self.run_install(
            "--no-notifications",
            "--no-codex-routing",
            "update",
            home=home,
        )
        output = result.stdout.decode()
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn("GPU Broker companion source is unavailable", output)
        self.assertFalse((home / ".agents").exists())
        self.assertFalse((home / ".cursor").exists())
        self.assertFalse((home / ".claude").exists())

    def test_all_install_can_refresh_owned_writer_agents(self) -> None:
        home = self.base / "all-install-idempotent"
        first = self.run_install("all", home=home)
        self.assertEqual(first.returncode, 0, first.stdout.decode())

        second = self.run_install("all", home=home)
        self.assertEqual(second.returncode, 0, second.stdout.decode())

        for relative in (
            ".cursor/agents/writer.md",
            ".claude/agents/writer.md",
        ):
            with self.subTest(agent=relative):
                rendered = (home / relative).read_text(encoding="utf-8")
                self.assertIn("name: writer\n", rendered)
                self.assertIn("You are the Teamwork Writer leaf role.", rendered)
                self.assertIn("Do not spawn or delegate.", rendered)

        codex_writer = (
            home / ".codex" / "agents" / "teamwork-writer.toml"
        ).read_text(encoding="utf-8")
        self.assertIn('name = "teamwork_writer"', codex_writer)
        self.assertIn("Do not spawn or delegate.", codex_writer)

    def test_all_install_can_refresh_owned_debugger_agents(self) -> None:
        home = self.base / "all-install-debugger-idempotent"
        first = self.run_install("all", home=home)
        self.assertEqual(first.returncode, 0, first.stdout.decode())

        second = self.run_install("all", home=home)
        self.assertEqual(second.returncode, 0, second.stdout.decode())

        for relative in (
            ".cursor/agents/debugger.md",
            ".claude/agents/debugger.md",
        ):
            with self.subTest(agent=relative):
                rendered = (home / relative).read_text(encoding="utf-8")
                self.assertIn("name: debugger\n", rendered)
                self.assertIn("You are Teamwork Debugger.", rendered)
                self.assertIn("Do not spawn or delegate.", rendered)

    def test_owned_skill_content_drift_is_refreshed(self) -> None:
        home = self.base / "drifted-home"
        installed = self.run_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(installed.returncode, 0, installed.stdout.decode())

        skill = home / ".agents" / "skills" / "teamwork-collaborate" / "SKILL.md"
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
        self.assertTrue(
            (home / ".agents" / "skills" / "teamwork-collaborate" / "SKILL.md").is_file()
        )

    def test_exact_owned_v46_grill_is_retired_on_all_three_hosts(self) -> None:
        for platform in ("codex", "cursor", "claude"):
            with self.subTest(platform=platform):
                home = self.base / f"exact-v46-grill-{platform}"
                skill = self.install_exact_v46_grill(home, platform)
                args = (
                    ("--no-codex-routing", "codex")
                    if platform == "codex"
                    else (platform,)
                )

                result = self.run_install(*args, home=home)

                self.assertEqual(result.returncode, 0, result.stdout.decode())
                self.assertFalse(skill.parent.exists())
                self.assertTrue(
                    (
                        home
                        / PLATFORM_SKILL_ROOTS[platform]
                        / "teamwork-collaborate"
                        / "SKILL.md"
                    ).is_file()
                )

    def test_modified_v46_grill_blocks_upgrade_and_is_preserved(self) -> None:
        for platform in ("codex", "cursor", "claude"):
            with self.subTest(platform=platform):
                home = self.base / f"modified-v46-grill-{platform}"
                skill = self.install_exact_v46_grill(home, platform)
                skill.write_bytes(skill.read_bytes() + b"\nuser change\n")
                before = skill.read_bytes()
                args = (
                    ("--no-codex-routing", "codex")
                    if platform == "codex"
                    else (platform,)
                )

                result = self.run_install(*args, home=home)

                self.assertNotEqual(result.returncode, 0, result.stdout.decode())
                self.assertIn("unknown files in grill-me", result.stdout.decode())
                self.assertEqual(before, skill.read_bytes())
                self.assertFalse(
                    (
                        home
                        / PLATFORM_SKILL_ROOTS[platform]
                        / "teamwork-collaborate"
                    ).exists()
                )

                readiness = self.run_readiness(home)
                self.assertNotEqual(readiness.returncode, 0, readiness.stdout)
                self.assertIn("INSTALL_READY=no", readiness.stdout)
                self.assertIn(f"{platform}-skill-content", readiness.stdout)

    def test_unmarked_v46_grill_blocks_upgrade_and_is_preserved(self) -> None:
        for platform in ("codex", "cursor", "claude"):
            with self.subTest(platform=platform):
                home = self.base / f"unmarked-v46-grill-{platform}"
                skill = self.install_exact_v46_grill(
                    home, platform, ownership_markers=False
                )
                before = skill.read_bytes()
                args = (
                    ("--no-codex-routing", "codex")
                    if platform == "codex"
                    else (platform,)
                )

                result = self.run_install(*args, home=home)

                self.assertNotEqual(result.returncode, 0, result.stdout.decode())
                self.assertIn(
                    "without Teamwork ownership markers", result.stdout.decode()
                )
                self.assertEqual(before, skill.read_bytes())

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

    def test_exact_owned_v5_retired_skills_are_removed(self) -> None:
        for retired in ("grill-me", "teamwork-design", "using-teamwork", "teamwork-execute", "teamwork"):
            with self.subTest(retired=retired):
                home = self.base / f"exact-retired-{retired}"
                skill_root = self.install_retired_from_fixture(home, "codex", retired)

                result = self.run_install("--no-codex-routing", "codex", home=home)

                self.assertEqual(result.returncode, 0, result.stdout.decode())
                self.assertFalse(skill_root.exists())
                self.assertTrue(
                    (home / ".agents/skills/teamwork-collaborate/SKILL.md").is_file()
                )

    def test_teamwork_discuss_has_no_retired_deletion_authority(self) -> None:
        home = self.base / "no-source-discuss"
        skill = home / ".agents/skills/teamwork-discuss/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            "---\nname: teamwork-discuss\ndescription: Use when discussing.\n---\n",
            encoding="utf-8",
        )
        root = home / ".agents/skills"
        (root / ".teamwork-version").write_text("4.6.0\n", encoding="utf-8")
        (root / ".teamwork-profile").write_text("performance-first\n", encoding="utf-8")
        before = skill.read_bytes()

        result = self.run_install("--no-codex-routing", "codex", home=home)

        self.assertNotEqual(result.returncode, 0, result.stdout.decode())
        self.assertIn(
            "No frozen Teamwork-owned manifest is allowed for teamwork-discuss",
            result.stdout.decode(),
        )
        self.assertEqual(skill.read_bytes(), before)
        self.assertFalse((root / "teamwork-collaborate").exists())

    def test_tampered_retired_fixture_copy_blocks_and_preserves_tree(self) -> None:
        cases = (
            ("teamwork-design", "content"),
            ("using-teamwork", "mode"),
            ("teamwork", "extra"),
        )
        for retired, tamper in cases:
            with self.subTest(retired=retired, tamper=tamper):
                home = self.base / f"tampered-{retired}-{tamper}"
                skill_root = self.install_retired_from_fixture(home, "codex", retired)
                if tamper == "content":
                    target = skill_root / "SKILL.md"
                    target.write_bytes(target.read_bytes() + b"user change\n")
                elif tamper == "mode":
                    (skill_root / "SKILL.md").chmod(0o600)
                else:
                    (skill_root / "user-notes.md").write_text(
                        "preserve\n", encoding="utf-8"
                    )
                before = {
                    path.relative_to(home).as_posix(): (
                        path.stat().st_mode & 0o777,
                        path.read_bytes(),
                    )
                    for path in home.rglob("*")
                    if path.is_file()
                }

                result = self.run_install("--no-codex-routing", "codex", home=home)

                self.assertNotEqual(result.returncode, 0, result.stdout.decode())
                self.assertIn(f"unknown files in {retired}", result.stdout.decode())
                after = {
                    path.relative_to(home).as_posix(): (
                        path.stat().st_mode & 0o777,
                        path.read_bytes(),
                    )
                    for path in home.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(after, before)
                self.assertFalse(
                    (home / ".agents/skills/teamwork-collaborate").exists()
                )


class ManagedDependencyHealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        status = self.path.rsplit("/", 1)[-1]
        if status not in {"live", "ready"}:
            self.send_error(404)
            return
        body = f'{{"status":"{status}"}}'.encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


class ManagedUpdateTargetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tempdir.name)
        self.bin_dir = self.base / "bin"
        self.bin_dir.mkdir()
        self.log = self.base / "commands.log"
        self.source = self.base / "gpu-broker"
        self.source.mkdir()
        (self.source / "pyproject.toml").write_text(
            "[project]\nname='gpu-broker'\n", encoding="utf-8"
        )
        self.server = socketserver.TCPServer(
            ("127.0.0.1", 0), ManagedDependencyHealthHandler
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.thread.start()
        self.write_command(
            "codegraph",
            """case \"${1:-}\" in
  --version|version) echo 'codegraph 1.5.0' ;;
  upgrade) echo \"codegraph $*\" >> \"$TEAMWORK_TEST_LOG\" ;;
esac
""",
        )
        self.write_command(
            "npm",
            """echo \"npm $*\" >> \"$TEAMWORK_TEST_LOG\"
cat > \"$TEAMWORK_TEST_BIN/codegraph\" <<'EOF'
#!/usr/bin/env bash
case \"${1:-}\" in
  --version|version) echo 'codegraph 1.5.0' ;;
  upgrade) echo \"codegraph $*\" >> \"$TEAMWORK_TEST_LOG\" ;;
esac
EOF
chmod 755 \"$TEAMWORK_TEST_BIN/codegraph\"
""",
        )
        self.write_command("uv", "echo \"uv $*\" >> \"$TEAMWORK_TEST_LOG\"\n")
        self.write_command(
            "gpu-broker",
            """case \"${1:-}/${2:-}\" in
  daemon/status) echo '{}' ;;
  daemon/install) echo \"gpu-broker $*\" >> \"$TEAMWORK_TEST_LOG\" ;;
  *) exit 2 ;;
esac
""",
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tempdir.cleanup()

    def write_command(self, name: str, body: str) -> None:
        command = self.bin_dir / name
        command.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n" + body,
            encoding="utf-8",
        )
        command.chmod(0o755)

    def managed_update_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.base / "home")
        # Keep the test independent of a developer's globally installed CodeGraph.
        env["PATH"] = f"{self.bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin"
        env["TEAMWORK_TEST_LOG"] = str(self.log)
        env["TEAMWORK_TEST_BIN"] = str(self.bin_dir)
        env["TEAMWORK_GPU_BROKER_SOURCE"] = str(self.source)
        env["TEAMWORK_GPU_BROKER_URL"] = (
            f"http://127.0.0.1:{self.server.server_address[1]}"
        )
        return env

    def run_managed_update(self) -> subprocess.CompletedProcess[str]:
        env = self.managed_update_env()
        result = subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "install.sh"),
                "--no-notifications",
                "--no-codex-routing",
                "update",
            ],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        return result

    def test_update_refreshes_dependencies_before_global_surfaces(self) -> None:
        result = self.run_managed_update()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(
            (
                self.base
                / "home"
                / ".agents"
                / "skills"
                / "teamwork-update"
                / "SKILL.md"
            ).is_file()
        )
        self.assertTrue((self.base / "home" / ".cursor" / "mcp.json").is_file())
        commands = self.log.read_text(encoding="utf-8")
        self.assertIn("codegraph upgrade 1.5.0", commands)
        self.assertIn(f"uv tool install --force {self.source}", commands)
        self.assertIn(
            f"gpu-broker daemon install --source-root {self.source}", commands
        )

    def test_update_installs_missing_codegraph(self) -> None:
        (self.bin_dir / "codegraph").unlink()
        result = self.run_managed_update()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.bin_dir / "codegraph").is_file())
        commands = self.log.read_text(encoding="utf-8")
        self.assertIn("npm install --global @colbymchenry/codegraph@1.5.0", commands)


if __name__ == "__main__":
    unittest.main()
