#!/usr/bin/env python3
"""Installer contract tests for the current Teamwork release surface."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
V630_DESIGNER_FIXTURE = REPO_ROOT / "scripts/tests/fixtures/v6.3.0-teamwork-designer.toml"
V630_WRITER_FIXTURE = REPO_ROOT / "scripts/tests/fixtures/v6.3.0-teamwork-writer.toml"
EXPLICIT_BASELINE = (
    "--profile",
    "performance-first",
)
EXPECTED_SKILLS = {
    "teamwork-collaborate",
    "teamwork-debug",
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
    "teamwork-challenger.toml",
    "teamwork-planner.toml",
    "teamwork-worker.toml",
    "teamwork-writer.toml",
    "teamwork-reviewer.toml",
}
CODEX_PROFILE_MATRICES = {
    "performance-first": {
        "teamwork-researcher": ("gpt-5.6-terra", "high"),
        "teamwork-explorer": ("gpt-5.6-terra", "high"),
        "teamwork-debugger": ("gpt-5.6-sol", "high"),
        "teamwork-challenger": ("gpt-5.6-sol", "high"),
        "teamwork-planner": ("gpt-5.6-sol", "high"),
        "teamwork-worker": ("gpt-5.6-terra", "high"),
        "teamwork-writer": ("gpt-5.6-luna", "high"),
        "teamwork-reviewer": ("gpt-5.6-sol", "max"),
    },
    "cost-first": {
        "teamwork-researcher": ("gpt-5.6-terra", "high"),
        "teamwork-explorer": ("gpt-5.6-luna", "high"),
        "teamwork-debugger": ("gpt-5.6-terra", "high"),
        "teamwork-challenger": ("gpt-5.6-terra", "high"),
        "teamwork-planner": ("gpt-5.6-terra", "high"),
        "teamwork-worker": ("gpt-5.6-luna", "xhigh"),
        "teamwork-writer": ("gpt-5.6-luna", "high"),
        "teamwork-reviewer": ("gpt-5.6-sol", "high"),
    },
}


class InstallCliCurrentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tempdir.name).resolve()
        self.fixture = self.base / "fixture"
        self.fixture.mkdir()
        for path in ("install.sh", "VERSION"):
            shutil.copy2(REPO_ROOT / path, self.fixture / path)
        for directory in ("hooks", "config", "policy", "skills", "templates"):
            shutil.copytree(REPO_ROOT / directory, self.fixture / directory)
        (self.fixture / "scripts").mkdir()
        for path in (
            "check-update.sh",
            "configure-codex-routing.py",
            "configure-notifications.py",
            "codex_routing_config.py",
            "init-project-files.py",
            "init-project.sh",
            "plugin-activation.py",
            "teamwork_index_v4.py",
            "migrate-teamwork-documents.py",
            "validate_teamwork_index.py",
        ):
            source = REPO_ROOT / "scripts" / path
            destination = self.fixture / "scripts" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        shutil.copytree(REPO_ROOT / "scripts/install", self.fixture / "scripts/install")
        shutil.copytree(REPO_ROOT / "scripts/teamwork_tooling", self.fixture / "scripts/teamwork_tooling")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_install(
        self,
        *args: str,
        home: pathlib.Path | None = None,
        create_home: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        env = os.environ.copy()
        for key in tuple(env):
            if key.startswith("TEAMWORK_"):
                env.pop(key)
        env["HOME"] = str(home or (self.base / "home"))
        env["CODEX_HOME"] = str(pathlib.Path(env["HOME"]) / ".codex")
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

    def run_lifecycle_install(self, *args: str, home: pathlib.Path) -> subprocess.CompletedProcess[bytes]:
        return self.run_install(*EXPLICIT_BASELINE, *args, home=home)

    def test_help_exposes_current_update_contract(self) -> None:
        result = self.run_install("--help")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("codex|cursor|claude|all|update|init-project|plugin-codex-bootstrap", output)
        self.assertIn("Refresh all Teamwork global surfaces", output)
        self.assertIn("$teamwork-update must complete", output)
        self.assertIn("`--project-root` is valid with `update`, `init-project`, or `plugin-init-project`.", output)
        self.assertIn("Challenger", output)
        self.assertNotIn("Plan Reviewer", output)
        self.assertNotIn("v3.4.2", output)
        self.assertNotIn("frozen", output.lower())

    def test_external_integrations_are_not_part_of_the_runtime_flow(self) -> None:
        runtime_sources = [
            REPO_ROOT / "install.sh",
            REPO_ROOT / "scripts/check-update.sh",
            REPO_ROOT / "scripts/init-project.sh",
            REPO_ROOT / "scripts/init-project-files.py",
            *sorted((REPO_ROOT / "skills").rglob("SKILL.md")),
            *sorted((REPO_ROOT / "templates").rglob("*")),
        ]
        forbidden = ("codegraph", "gpu-broker", "gpu_broker", "serverpilot")
        for source in runtime_sources:
            if not source.is_file():
                continue
            content = source.read_text(encoding="utf-8").lower()
            self.assertFalse(
                any(term in content for term in forbidden),
                f"external integration leaked into runtime flow: {source.relative_to(REPO_ROOT)}",
            )

        result = self.run_install("--managed-codegraph", "codex")
        self.assertEqual(result.returncode, 2, result.stdout.decode())
        self.assertIn("Unknown argument", result.stdout.decode())

    def test_project_root_is_accepted_only_by_project_update_targets(self) -> None:
        project = self.base / "project-root-only"
        project.mkdir()
        result = self.run_install("--project-root", str(project), "codex")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 2, output)
        self.assertIn("--project-root is valid only with update, init-project, or plugin-init-project.", output)

    def test_current_codex_install_copies_only_public_current_skills(self) -> None:
        home = self.base / "user-home"
        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        skill_root = home / ".agents/skills"
        self.assertEqual({path.name for path in skill_root.iterdir() if path.is_dir()}, EXPECTED_SKILLS)
        for retired in ("grill-me", "using-teamwork", "teamwork", "teamwork-execute", "teamwork-design", "teamwork-discuss", "teamwork-explore"):
            self.assertFalse((skill_root / retired).exists(), retired)
        self.assertEqual(
            {path.name for path in (home / ".codex/agents").iterdir() if path.is_file()},
            EXPECTED_CODEX_AGENTS,
        )
        self.assertTrue((home / ".codex/AGENTS.md").is_file())

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
            for agent, (model, effort) in matrix.items():
                rendered = (home / ".codex/agents" / f"{agent}.toml").read_text(encoding="utf-8")
                self.assertIn(f'model = "{model}"', rendered)
                self.assertIn(f'model_reasoning_effort = "{effort}"', rendered)

    def test_removed_profile_alias_fails_closed(self) -> None:
        result = self.run_install("--profile", "gpt56-role", "codex-agents")
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 2, output)
        self.assertIn("Unknown profile: gpt56-role", output)

    def test_teamwork_marked_retired_skill_is_deleted_without_byte_fixture(self) -> None:
        home = self.base / "retired-skill-home"
        root = home / ".agents/skills"
        retired = root / "teamwork-explore"
        retired.mkdir(parents=True)
        (retired / "SKILL.md").write_text(
            "---\nname: teamwork-explore\ndescription: Use when old Teamwork Explore.\n---\n\nlocal edits\n",
            encoding="utf-8",
        )
        (root / ".teamwork-version").write_text("6.3.0\n", encoding="utf-8")
        (root / ".teamwork-profile").write_text("performance-first\n", encoding="utf-8")

        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        self.assertFalse(retired.exists())
        self.assertTrue((root / "teamwork-collaborate/SKILL.md").is_file())

    def test_unmarked_generic_teamwork_skill_is_never_claimed_as_legacy(self) -> None:
        home = self.base / "generic-teamwork-home"
        skill = home / ".codex/skills/teamwork/SKILL.md"
        skill.parent.mkdir(parents=True)
        original = (
            "---\n"
            "name: teamwork\n"
            "description: Use when selecting a user-owned Teamwork method.\n"
            "---\n"
        )
        skill.write_text(original, encoding="utf-8")

        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(result.returncode, 0, result.stdout.decode())
        self.assertEqual(skill.read_text(encoding="utf-8"), original)

    def test_marked_current_skill_with_missing_skill_file_is_repaired(self) -> None:
        home = self.base / "missing-current-skill-file-home"
        first = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(first.returncode, 0, first.stdout.decode())

        skill_file = home / ".agents/skills/teamwork-collaborate/SKILL.md"
        skill_file.unlink()

        repaired = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
        self.assertEqual(repaired.returncode, 0, repaired.stdout.decode())
        self.assertEqual(
            skill_file.read_text(encoding="utf-8"),
            (REPO_ROOT / "skills/teamwork-collaborate/SKILL.md").read_text(encoding="utf-8"),
        )

    def test_unknown_file_inside_marked_legacy_skill_blocks_cleanup(self) -> None:
        home = self.base / "legacy-skill-with-user-file"
        root = home / ".codex/skills"
        shutil.copytree(
            REPO_ROOT / "skills/teamwork-collaborate",
            root / "teamwork-collaborate",
        )
        (root / ".teamwork-version").write_text("6.3.0\n", encoding="utf-8")
        (root / ".teamwork-profile").write_text("performance-first\n", encoding="utf-8")
        note = root / "teamwork-collaborate/user-note.md"
        note.write_text("user-owned\n", encoding="utf-8")

        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
        self.assertNotEqual(result.returncode, 0, result.stdout.decode())
        self.assertEqual(note.read_text(encoding="utf-8"), "user-owned\n")
        self.assertFalse((home / ".agents/skills/teamwork-collaborate").exists())

    def test_unmarked_same_named_skill_is_not_claimed(self) -> None:
        home = self.base / "unmarked-skill-home"
        skill = home / ".agents/skills/teamwork-collaborate/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            "---\nname: teamwork-collaborate\ndescription: User-owned skill.\n---\n",
            encoding="utf-8",
        )

        result = self.run_lifecycle_install("--no-codex-routing", "codex", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 1, output)
        self.assertIn("without Teamwork ownership markers", output)

    def test_unowned_same_named_agent_is_not_claimed(self) -> None:
        home = self.base / "unowned-agent-home"
        agent = home / ".codex/agents/teamwork-researcher.toml"
        agent.parent.mkdir(parents=True)
        agent.write_text('name = "teamwork_researcher"\nprompt = "user-owned"\n', encoding="utf-8")

        result = self.run_install("--no-codex-routing", "codex-agents", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 1, output)
        self.assertIn("not a recognized Teamwork-owned profile", output)
        self.assertIn("user-owned", agent.read_text(encoding="utf-8"))

    def test_v630_writer_agent_is_preserved_without_current_ownership(self) -> None:
        home = self.base / "v630-writer-home"
        agent = home / ".codex/agents/teamwork-writer.toml"
        agent.parent.mkdir(parents=True)
        shutil.copy2(V630_WRITER_FIXTURE, agent)

        result = self.run_install("--no-codex-routing", "codex-agents", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 1, output)
        self.assertIn("not a recognized Teamwork-owned profile", output)
        self.assertEqual(agent.read_text(encoding="utf-8"), V630_WRITER_FIXTURE.read_text(encoding="utf-8"))

    def test_update_preserves_v630_writer_without_current_ownership(self) -> None:
        home = self.base / "v630-writer-update-home"
        project = self.base / "v630-writer-update-project"
        project.mkdir()
        init = self.run_install("--project-root", str(project), "init-project", home=home)
        self.assertEqual(init.returncode, 0, init.stdout.decode())
        agent = home / ".codex/agents/teamwork-writer.toml"
        agent.parent.mkdir(parents=True)
        shutil.copy2(V630_WRITER_FIXTURE, agent)

        result = self.run_lifecycle_install(
            "--project-root",
            str(project),
            "--no-codex-routing",
            "update",
            home=home,
        )
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 1, output)
        self.assertIn("not a recognized Teamwork-owned profile", output)
        self.assertEqual(agent.read_text(encoding="utf-8"), V630_WRITER_FIXTURE.read_text(encoding="utf-8"))

    def test_v630_designer_agent_is_preserved(self) -> None:
        home = self.base / "v630-designer-home"
        agent = home / ".codex/agents/teamwork-designer.toml"
        agent.parent.mkdir(parents=True)
        shutil.copy2(V630_DESIGNER_FIXTURE, agent)

        result = self.run_install("--no-codex-routing", "codex-agents", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertTrue(agent.exists())
        self.assertIn("Preserved retired agent conflict", output)

    def test_update_preserves_v630_designer_agent(self) -> None:
        home = self.base / "v630-designer-update-home"
        project = self.base / "v630-designer-update-project"
        project.mkdir()
        init = self.run_install("--project-root", str(project), "init-project", home=home)
        self.assertEqual(init.returncode, 0, init.stdout.decode())
        agent = home / ".codex/agents/teamwork-designer.toml"
        agent.parent.mkdir(parents=True)
        shutil.copy2(V630_DESIGNER_FIXTURE, agent)

        result = self.run_lifecycle_install(
            "--project-root",
            str(project),
            "--no-codex-routing",
            "update",
            home=home,
        )
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("global updated; schema-v4 project context current", output)
        self.assertTrue(agent.exists())

    def test_official_v630_designer_symlink_is_preserved(self) -> None:
        home = self.base / "v630-designer-symlink-home"
        legacy_template = home / "legacy/templates/codex-agents/teamwork-designer.toml"
        legacy_template.parent.mkdir(parents=True)
        shutil.copy2(V630_DESIGNER_FIXTURE, legacy_template)
        agent = home / ".codex/agents/teamwork-designer.toml"
        agent.parent.mkdir(parents=True)
        agent.symlink_to(legacy_template)

        result = self.run_install("--no-codex-routing", "codex-agents", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertTrue(agent.is_symlink())
        self.assertEqual(agent.resolve(), legacy_template)

    def test_official_v630_designer_multi_hardlink_is_preserved(self) -> None:
        home = self.base / "v630-designer-hardlink-home"
        agent = home / ".codex/agents/teamwork-designer.toml"
        agent.parent.mkdir(parents=True)
        shutil.copy2(V630_DESIGNER_FIXTURE, agent)
        peer = agent.parent / "teamwork-designer-peer.toml"
        os.link(agent, peer)

        result = self.run_install("--no-codex-routing", "codex-agents", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertTrue(agent.exists())
        self.assertTrue(peer.exists())
        self.assertTrue(agent.samefile(peer))

    def test_same_named_designer_with_legacy_marker_is_not_claimed(self) -> None:
        home = self.base / "unowned-legacy-marker-designer-home"
        agent = home / ".codex/agents/teamwork-designer.toml"
        agent.parent.mkdir(parents=True)
        original = (
            'name = "teamwork_designer"\n'
            'developer_instructions = "You are the Teamwork Designer. user-owned"\n'
        )
        agent.write_text(original, encoding="utf-8")

        result = self.run_install("--no-codex-routing", "codex-agents", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertEqual(agent.read_text(encoding="utf-8"), original)

    def test_same_named_writer_with_legacy_marker_is_not_claimed(self) -> None:
        home = self.base / "unowned-legacy-marker-writer-home"
        agent = home / ".codex/agents/teamwork-writer.toml"
        agent.parent.mkdir(parents=True)
        original = (
            'name = "teamwork_writer"\n'
            'developer_instructions = "Do not spawn or delegate. user-owned"\n'
        )
        agent.write_text(original, encoding="utf-8")

        result = self.run_install("--no-codex-routing", "codex-agents", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 1, output)
        self.assertIn("not a recognized Teamwork-owned profile", output)
        self.assertEqual(agent.read_text(encoding="utf-8"), original)

    def test_update_without_project_root_reports_pending_migration(self) -> None:
        home = self.base / "update-no-project"
        result = self.run_lifecycle_install("--no-codex-routing", "update", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("global updated; schema-v4 project migration pending", output)

    def test_update_with_project_root_runs_current_project_migration(self) -> None:
        home = self.base / "update-project-home"
        project = self.base / "project"
        project.mkdir()
        init = self.run_install("--project-root", str(project), "init-project", home=home)
        self.assertEqual(init.returncode, 0, init.stdout.decode())

        result = self.run_lifecycle_install("--project-root", str(project), "--no-codex-routing", "update", home=home)
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("global updated; schema-v4 project context current", output)

    def test_update_reports_legacy_project_needs_semantic_migration(self) -> None:
        home = self.base / "update-failure-home"
        project = self.base / "failing-project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True)
        (memory / "index.json").write_text('{"schema_version":3}\n', encoding="utf-8")

        result = self.run_lifecycle_install(
            "--project-root",
            str(project),
            "--no-codex-routing",
            "update",
            home=home,
        )
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 3, output)
        self.assertIn("schema-v4 semantic project migration required", output)
        self.assertIn("project documents were not changed", output)
        self.assertNotIn("project migration complete", output)

    def test_update_propagates_project_context_refresh_failure(self) -> None:
        home = self.base / "update-context-failure-home"
        project = self.base / "context-failing-project"
        project.mkdir()
        init = self.run_install("--project-root", str(project), "init-project", home=home)
        self.assertEqual(init.returncode, 0, init.stdout.decode())
        (self.fixture / "scripts/init-project-files.py").write_text(
            "import sys\nsys.stderr.write('fixture context failure\\n')\nsys.exit(9)\n",
            encoding="utf-8",
        )

        result = self.run_lifecycle_install(
            "--project-root",
            str(project),
            "--no-codex-routing",
            "update",
            home=home,
        )
        output = result.stdout.decode()
        self.assertEqual(result.returncode, 9, output)
        self.assertIn("schema-v4 project context refresh failed", output)
        self.assertNotIn("project migration complete", output)


if __name__ == "__main__":
    unittest.main()
