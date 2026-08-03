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
PREFERENCES_HELPER = REPO_ROOT / "scripts/install/preferences.py"
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
        "teamwork-researcher": ("gpt-5.6-terra", "high"),
        "teamwork-explorer": ("gpt-5.6-terra", "high"),
        "teamwork-debugger": ("gpt-5.6-sol", "high"),
        "teamwork-designer": ("gpt-5.6-sol", "high"),
        "teamwork-planner": ("gpt-5.6-sol", "high"),
        "teamwork-worker": ("gpt-5.6-terra", "high"),
        "teamwork-writer": ("gpt-5.6-luna", "high"),
        "teamwork-plan-reviewer": ("gpt-5.6-sol", "high"),
        "teamwork-reviewer": ("gpt-5.6-sol", "max"),
    },
    "cost-first": {
        "teamwork-researcher": ("gpt-5.6-terra", "high"),
        "teamwork-explorer": ("gpt-5.6-luna", "high"),
        "teamwork-debugger": ("gpt-5.6-terra", "high"),
        "teamwork-designer": ("gpt-5.6-terra", "high"),
        "teamwork-planner": ("gpt-5.6-terra", "high"),
        "teamwork-worker": ("gpt-5.6-luna", "xhigh"),
        "teamwork-writer": ("gpt-5.6-luna", "high"),
        "teamwork-plan-reviewer": ("gpt-5.6-terra", "high"),
        "teamwork-reviewer": ("gpt-5.6-sol", "high"),
    },
}
EXPLICIT_BASELINE = (
    "--profile",
    "performance-first",
    "--no-managed-codegraph",
    "--no-managed-gpu-broker",
)


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
        shutil.copy2(
            REPO_ROOT / "scripts" / "plugin-activation.py",
            self.fixture / "scripts" / "plugin-activation.py",
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
        env.pop("TEAMWORK_MANAGED_CODEGRAPH", None)
        env.pop("TEAMWORK_MANAGED_GPU_BROKER", None)
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

    def run_lifecycle_install(
        self,
        *args: str,
        home: pathlib.Path | None = None,
        create_home: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        return self.run_install(
            *EXPLICIT_BASELINE,
            *args,
            home=home,
            create_home=create_home,
        )

    def make_fixture_marketplace_runtime(self) -> None:
        (self.fixture / ".teamwork-plugin-runtime").write_text(
            "TEAMWORK_CODEX_PLUGIN_RUNTIME=1",
            encoding="utf-8",
        )
        manifest_root = self.fixture / ".codex-plugin"
        manifest_root.mkdir()
        shutil.copy2(REPO_ROOT / ".codex-plugin" / "plugin.json", manifest_root / "plugin.json")

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
        self.assertIn("--managed-codegraph|--no-managed-codegraph", output)
        self.assertIn("--managed-gpu-broker|--no-managed-gpu-broker", output)
        self.assertIn(
            "`--project-root` is valid only with `init-project` or `plugin-init-project`.",
            output,
        )
        self.assertNotIn("project-codex-agents", output)
        self.assertNotRegex(output, r"(?m)^\s+project\s+")
        self.assertNotIn("init-project refreshes the user-level routing", output)
        self.assertIn("Project init never changes user-level routing", output)
        self.assertIn("cost-first uses Terra/high", output)
        self.assertIn("Luna/high for Explorer and Writer;", output)
        self.assertIn("Luna/xhigh for Worker; and Sol/high for Reviewer.", output)
        self.assertIn("Cursor and Claude Code keep", output)
        self.assertIn("their existing profile mappings.", output)
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

    def test_managed_capability_flags_are_rejected_by_non_lifecycle_targets(self) -> None:
        targets = (
            "cursor",
            "claude",
            "init-project",
            "plugin-init-project",
            "codex-agents",
            "cursor-agents",
            "claude-agents",
            "codex-policy",
            "cursor-policy",
            "cursor-policy-copy",
            "claude-policy",
            "cursor-mcp",
        )
        flags = (
            "--dependencies",
            "--no-dependencies",
            "--managed-codegraph",
            "--no-managed-codegraph",
            "--managed-gpu-broker",
            "--no-managed-gpu-broker",
        )
        for target in targets:
            for flag in flags:
                with self.subTest(target=target, flag=flag):
                    home = self.base / f"unsupported-{target}-{flag.removeprefix('--')}"
                    result = self.run_install(flag, target, home=home)
                    output = result.stdout.decode()
                    self.assertEqual(result.returncode, 2, output)
                    self.assertIn(
                        "Managed capability options are supported only with codex, all, update, or plugin-codex-bootstrap targets",
                        output,
                    )
                    self.assertFalse(
                        (home / ".local/state/teamwork/install-preferences.json").exists()
                    )

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

    def test_narrow_agent_target_does_not_create_missing_capability_receipt(self) -> None:
        home = self.base / "narrow-agent-no-receipt"
        result = self.run_install(
            "--profile",
            "cost-first",
            "--no-codex-routing",
            "codex-agents",
            home=home,
        )
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        rendered = (home / ".codex/agents/teamwork-worker.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn('model = "gpt-5.6-luna"', rendered)
        self.assertFalse(
            (home / ".local/state/teamwork/install-preferences.json").exists()
        )

    def test_removed_profile_alias_fails_closed(self) -> None:
        result = self.run_install("--profile", "gpt56-role", "codex-agents")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 2, output)
        self.assertIn("Unknown profile: gpt56-role", output)

    def test_user_copy_installs_keep_policy_destinations(self) -> None:
        home = self.base / "user-home"
        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
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
            "--no-managed-codegraph",
            "--no-managed-gpu-broker",
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
            "--profile",
            "performance-first",
            "--dependencies",
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

    def test_checkout_update_with_plugin_activation_uses_checkout_safe_path(self) -> None:
        home = self.base / "checkout-update-with-plugin-activation"
        activation = home / ".codex/teamwork/plugin-activation.json"
        activation.parent.mkdir(parents=True)
        marker = {
            "schema_version": 1,
            "plugin": "teamwork-skill",
            "marketplace": "teamwork",
            "version": "6.1.3",
            "profile": "performance-first",
            "notifications": "enabled",
        }
        activation.write_text(json.dumps(marker), encoding="utf-8")
        before = activation.read_bytes()

        result = self.run_install(
            "--profile",
            "performance-first",
            "--no-managed-codegraph",
            "--no-managed-gpu-broker",
            "--no-mcp",
            "update",
            home=home,
        )

        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertNotIn("must run from the Teamwork Marketplace runtime", output)
        self.assertIn("checkout update refreshed Codex plugin-managed global setup", output)
        self.assertEqual(before, activation.read_bytes())
        self.assertFalse((home / ".agents/skills").exists())
        self.assertTrue((home / ".codex/agents/teamwork-worker.toml").is_file())
        self.assertTrue((home / ".codex/AGENTS.md").is_file())
        self.assertTrue((home / ".cursor/skills/teamwork-update/SKILL.md").is_file())
        self.assertTrue((home / ".claude/skills/teamwork-update/SKILL.md").is_file())

    def test_plugin_runtime_update_without_activation_bootstraps_without_codex_skill_copy(self) -> None:
        self.make_fixture_marketplace_runtime()
        home = self.base / "plugin-runtime-update-no-activation"
        activation = home / ".codex/teamwork/plugin-activation.json"

        result = self.run_install(
            "--profile",
            "cost-first",
            "--no-managed-codegraph",
            "--no-managed-gpu-broker",
            "--no-notifications",
            "--no-mcp",
            "update",
            home=home,
        )

        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("Activated Teamwork Codex plugin", output)
        self.assertFalse((home / ".agents/skills").exists())
        self.assertTrue((home / ".codex/agents/teamwork-worker.toml").is_file())
        marker = json.loads(activation.read_text(encoding="utf-8"))
        self.assertEqual(marker["version"], (self.fixture / "VERSION").read_text(encoding="utf-8").strip())
        self.assertEqual(marker["profile"], "cost-first")
        self.assertEqual(marker["notifications"], "disabled")
        state = json.loads(
            (home / ".local/state/teamwork/install-preferences.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(state["desired"]["profile"]["value"], "cost-first")
        self.assertEqual(state["desired"]["codegraph"]["value"], "disabled")
        self.assertEqual(state["desired"]["gpu_broker"]["value"], "disabled")

    def test_all_install_can_refresh_owned_writer_agents(self) -> None:
        home = self.base / "all-install-idempotent"
        first = self.run_lifecycle_install("all", home=home)
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
        first = self.run_lifecycle_install("all", home=home)
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
        installed = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
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

        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
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

                if platform == "codex":
                    result = self.run_lifecycle_install(*args, home=home)
                else:
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

                if platform == "codex":
                    result = self.run_lifecycle_install(*args, home=home)
                else:
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

                if platform == "codex":
                    result = self.run_lifecycle_install(*args, home=home)
                else:
                    result = self.run_install(*args, home=home)

                self.assertNotEqual(result.returncode, 0, result.stdout.decode())
                self.assertIn(
                    "without Teamwork ownership markers", result.stdout.decode()
                )
                self.assertEqual(before, skill.read_bytes())

    def test_exact_v342_generic_router_is_removed(self) -> None:
        home = self.base / "exact-legacy-router-home"
        router = self.install_exact_v342_generic_router(home)

        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)

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

                result = self.run_lifecycle_install(
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

                result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)

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

        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)

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

                result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)

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


class InstallPreferenceHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tempdir.name)
        self.home = self.base / "home"
        self.state_root = self.base / "state"
        self.home.mkdir()
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["XDG_STATE_HOME"] = str(self.state_root)
        self.env["CODEX_HOME"] = str(self.home / ".codex")
        self.path = self.state_root / "teamwork" / "install-preferences.json"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_helper(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(PREFERENCES_HELPER), *args],
            cwd=REPO_ROOT,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_missing_preferences_are_read_only_until_recorded_and_then_inherited(self) -> None:
        missing = self.run_helper("resolve")
        self.assertEqual(missing.returncode, 0, missing.stderr)
        self.assertEqual(
            missing.stdout.strip(),
            "performance-first\tdisabled\tdisabled\tmissing",
        )
        self.assertFalse(self.path.exists())

        recorded = self.run_helper(
            "resolve",
            "--profile",
            "cost-first",
            "--profile-source",
            "cli",
            "--codegraph",
            "enabled",
            "--codegraph-source",
            "cli",
            "--record",
        )
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        state = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(state["owner"], "teamwork")
        self.assertEqual(state["desired"]["profile"]["value"], "cost-first")
        self.assertEqual(state["desired"]["codegraph"]["value"], "enabled")
        self.assertEqual(state["desired"]["gpu_broker"]["value"], "disabled")
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        inherited = self.run_helper("resolve")
        self.assertEqual(inherited.stdout.strip(), "cost-first\tenabled\tdisabled\tvalid")

    def test_invalid_or_unowned_preferences_are_never_overwritten(self) -> None:
        self.path.parent.mkdir(parents=True)
        original = b'{"schema_version":1,"owner":"someone-else"}\n'
        self.path.write_bytes(original)
        result = self.run_helper("resolve", "--record")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Teamwork install preferences refused", result.stderr)
        self.assertEqual(self.path.read_bytes(), original)
        status = self.run_helper("status", "--field", "status")
        self.assertEqual(status.stdout.strip(), "invalid")

    def test_plugin_activation_v1_seeds_profile_but_not_capabilities(self) -> None:
        activation = self.home / ".codex/teamwork/plugin-activation.json"
        activation.parent.mkdir(parents=True)
        activation.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "plugin": "teamwork-skill",
                    "marketplace": "teamwork",
                    "version": "6.1.3",
                    "profile": "cost-first",
                    "notifications": "disabled",
                }
            ),
            encoding="utf-8",
        )
        result = self.run_helper("resolve", "--record")
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(state["desired"]["profile"]["source"], "plugin-activation-v1")
        self.assertEqual(state["desired"]["profile"]["value"], "cost-first")
        self.assertEqual(state["desired"]["codegraph"]["value"], "disabled")
        self.assertEqual(state["desired"]["gpu_broker"]["value"], "disabled")


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
  --version|version) echo 'codegraph 0.9.6' ;;
esac
""",
        )
        self.write_command(
            "npm",
            """echo \"npm $*\" >> \"$TEAMWORK_TEST_LOG\"
target_bin=\"$TEAMWORK_TEST_BIN\"
if [[ \"${1:-}\" == install && \"${2:-}\" == --global && \"${3:-}\" == --force && \"${4:-}\" == --prefix ]]; then
  target_bin=\"${5}/bin\"
fi
mkdir -p \"$target_bin\"
cat > \"$target_bin/codegraph\" <<'EOF'
#!/usr/bin/env bash
case \"${1:-}\" in
  --version|version) echo 'codegraph 1.5.0' ;;
esac
EOF
chmod 755 \"$target_bin/codegraph\"
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

    def run_managed_update(
        self,
        env: dict[str, str] | None = None,
        *,
        capability_flags: tuple[str, ...] = ("--dependencies",),
        profile: str | None = "performance-first",
    ) -> subprocess.CompletedProcess[str]:
        env = env or self.managed_update_env()
        profile_flags = ("--profile", profile) if profile else ()
        result = subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "install.sh"),
                *profile_flags,
                *capability_flags,
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

    def preference_state(self) -> dict[str, object]:
        path = self.base / "home" / ".local" / "state" / "teamwork" / "install-preferences.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_update_requires_explicit_missing_preferences_before_writes(self) -> None:
        result = self.run_managed_update(capability_flags=(), profile=None)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("requires explicit profile", result.stderr)
        self.assertFalse(
            (
                self.base
                / "home"
                / ".local"
                / "state"
                / "teamwork"
                / "install-preferences.json"
            ).exists()
        )
        self.assertFalse((self.base / "home" / ".agents").exists())
        self.assertFalse((self.base / "home" / ".cursor").exists())
        self.assertFalse((self.base / "home" / ".claude").exists())

    def test_update_requires_explicit_capability_choices_when_profile_is_supplied(self) -> None:
        result = self.run_managed_update(capability_flags=())
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(
            "CodeGraph (--managed-codegraph|--no-managed-codegraph)",
            result.stderr,
        )
        self.assertIn(
            "GPU Broker (--managed-gpu-broker|--no-managed-gpu-broker)",
            result.stderr,
        )
        self.assertFalse(
            (
                self.base
                / "home"
                / ".local"
                / "state"
                / "teamwork"
                / "install-preferences.json"
            ).exists()
        )

    def test_update_baseline_skips_optional_tools_and_records_opt_out(self) -> None:
        result = self.run_managed_update(
            capability_flags=("--no-managed-codegraph", "--no-managed-gpu-broker")
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.log.exists())
        state = self.preference_state()
        self.assertEqual(state["desired"]["codegraph"]["value"], "disabled")
        self.assertEqual(state["desired"]["gpu_broker"]["value"], "disabled")
        self.assertEqual(state["receipts"]["codegraph"]["status"], "disabled")
        self.assertEqual(state["receipts"]["gpu_broker"]["status"], "disabled")

    def test_update_can_enable_codegraph_without_gpu_broker(self) -> None:
        result = self.run_managed_update(
            capability_flags=("--managed-codegraph", "--no-managed-gpu-broker")
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        commands = self.log.read_text(encoding="utf-8")
        self.assertIn("npm install --global @colbymchenry/codegraph@1.5.0", commands)
        self.assertNotIn("uv tool install", commands)
        self.assertNotIn("gpu-broker daemon install", commands)
        state = self.preference_state()
        self.assertEqual(state["desired"]["codegraph"]["value"], "enabled")
        self.assertEqual(state["receipts"]["codegraph"]["status"], "ready")
        self.assertEqual(state["desired"]["gpu_broker"]["value"], "disabled")

    def test_update_can_enable_gpu_broker_without_codegraph(self) -> None:
        result = self.run_managed_update(
            capability_flags=("--no-managed-codegraph", "--managed-gpu-broker")
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        commands = self.log.read_text(encoding="utf-8")
        self.assertNotIn("npm install", commands)
        self.assertIn(f"uv tool install --force {self.source}", commands)
        self.assertIn(
            f"gpu-broker daemon install --source-root {self.source}", commands
        )
        state = self.preference_state()
        self.assertEqual(state["desired"]["codegraph"]["value"], "disabled")
        self.assertEqual(state["desired"]["gpu_broker"]["value"], "enabled")
        self.assertEqual(state["receipts"]["gpu_broker"]["status"], "ready")

    def test_update_reuses_existing_valid_preferences_without_arguments(self) -> None:
        recorded = self.run_managed_update(
            capability_flags=("--no-managed-codegraph", "--no-managed-gpu-broker")
        )
        self.assertEqual(recorded.returncode, 0, recorded.stdout + recorded.stderr)
        reused = self.run_managed_update(capability_flags=(), profile=None)
        self.assertEqual(reused.returncode, 0, reused.stdout + reused.stderr)
        state = self.preference_state()
        self.assertEqual(state["desired"]["profile"]["value"], "performance-first")
        self.assertEqual(state["desired"]["codegraph"]["value"], "disabled")
        self.assertEqual(state["desired"]["gpu_broker"]["value"], "disabled")

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
        self.assertIn("npm install --global @colbymchenry/codegraph@1.5.0", commands)
        self.assertNotIn("codegraph upgrade", commands)
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

    def legacy_codegraph_env(self) -> tuple[dict[str, str], pathlib.Path]:
        home = self.base / "home"
        legacy_bin = home / ".local" / "bin"
        legacy_bin.mkdir(parents=True, exist_ok=True)
        legacy_codegraph = legacy_bin / "codegraph"
        legacy_codegraph.write_text(
            "#!/usr/bin/env bash\n"
            "case \"${1:-}\" in\n"
            "  --version|version) echo 'codegraph 0.9.6' ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        legacy_codegraph.chmod(0o755)
        (self.bin_dir / "codegraph").unlink()
        env = self.managed_update_env()
        env["PATH"] = f"{legacy_bin}:{self.bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin"
        return env, legacy_codegraph

    def test_update_replaces_effective_legacy_local_codegraph_shim(self) -> None:
        env, legacy_codegraph = self.legacy_codegraph_env()
        result = self.run_managed_update(env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        commands = self.log.read_text(encoding="utf-8")
        self.assertIn(
            "npm install --global --force --prefix "
            f"{self.base / 'home' / '.local'} @colbymchenry/codegraph@1.5.0",
            commands,
        )
        version = subprocess.run(
            [str(legacy_codegraph), "--version"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(version, "codegraph 1.5.0")

    def test_update_requires_npm_even_when_codegraph_is_present(self) -> None:
        (self.bin_dir / "npm").unlink()
        result = self.run_managed_update()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("npm is required to refresh managed CodeGraph", result.stderr)
        self.assertFalse((self.base / "home" / ".agents").exists())
        self.assertFalse((self.base / "home" / ".cursor").exists())
        self.assertFalse((self.base / "home" / ".claude").exists())

    def test_codegraph_install_failure_prevents_downstream_writes(self) -> None:
        self.write_command(
            "npm",
            "echo \"npm $*\" >> \"$TEAMWORK_TEST_LOG\"\nexit 1\n",
        )
        result = self.run_managed_update()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        commands = self.log.read_text(encoding="utf-8")
        self.assertIn("npm install --global @colbymchenry/codegraph@1.5.0", commands)
        self.assertNotIn("uv tool install", commands)
        self.assertNotIn("gpu-broker daemon install", commands)
        self.assertEqual(
            self.preference_state()["receipts"]["codegraph"]["status"],
            "failed",
        )
        self.assertFalse((self.base / "home" / ".agents").exists())
        self.assertFalse((self.base / "home" / ".cursor").exists())
        self.assertFalse((self.base / "home" / ".claude").exists())

    def test_legacy_shim_install_failure_prevents_downstream_writes(self) -> None:
        env, _ = self.legacy_codegraph_env()
        self.write_command(
            "npm",
            "echo \"npm $*\" >> \"$TEAMWORK_TEST_LOG\"\nexit 1\n",
        )
        result = self.run_managed_update(env)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        commands = self.log.read_text(encoding="utf-8")
        self.assertIn(
            "npm install --global --force --prefix "
            f"{self.base / 'home' / '.local'} @colbymchenry/codegraph@1.5.0",
            commands,
        )
        self.assertNotIn("uv tool install", commands)
        self.assertNotIn("gpu-broker daemon install", commands)
        self.assertFalse((self.base / "home" / ".agents").exists())
        self.assertFalse((self.base / "home" / ".cursor").exists())
        self.assertFalse((self.base / "home" / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
