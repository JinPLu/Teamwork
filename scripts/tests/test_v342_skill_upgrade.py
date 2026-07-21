#!/usr/bin/env python3
"""Regression coverage for the real v3.4.2-to-v4 skill migration."""

from __future__ import annotations

import io
import json
import os
import pathlib
import shutil
import subprocess
import tarfile
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "fixtures"
    / "v3.4.2-skill-inventory.json"
)
EXPECTED_V4_SKILLS = {
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
RETIRED_V342_SKILLS = {"using-teamwork", "teamwork-execute"}
RETIRED_AGENT_SAMPLE = {
    "codex": "teamwork-deep-judge.toml",
    "cursor": "deep-judge.md",
    "claude": "deep-judge.md",
}
EXPECTED_V4_REFERENCES = {
    "teamwork-debug/references/runtime-diagnosis.md",
    "teamwork-research/references/deep-research.md",
    "teamwork-review/references/strict-review.md",
}
PLATFORM_SKILL_ROOTS = {
    "codex": pathlib.Path(".agents/skills"),
    "cursor": pathlib.Path(".cursor/skills"),
    "claude": pathlib.Path(".claude/skills"),
}
PLATFORM_AGENT_ROOTS = {
    "codex": (pathlib.Path(".codex/agents"), "toml", {
        "teamwork-researcher", "teamwork-explorer", "teamwork-debugger",
        "teamwork-designer", "teamwork-planner", "teamwork-worker",
        "teamwork-plan-reviewer", "teamwork-reviewer",
    }),
    "cursor": (pathlib.Path(".cursor/agents"), "md", {
        "researcher", "explorer", "debugger", "designer", "planner",
        "worker", "plan-reviewer", "reviewer",
    }),
    "claude": (pathlib.Path(".claude/agents"), "md", {
        "researcher", "explorer", "debugger", "designer", "planner",
        "worker", "plan-reviewer", "reviewer",
    }),
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


class V342SkillUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.commit = cls.fixture["commit"]
        cls.tag = cls.fixture["tag"]

        commit_check = subprocess.run(
            ["git", "cat-file", "-e", f"{cls.commit}^{{commit}}"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if commit_check.returncode != 0:
            raise unittest.SkipTest(
                "frozen v3.4.2 commit is unavailable in this checkout; fetch tag "
                "v3.4.2 or provide the pinned commit object before running the "
                "upgrade fixture"
            )

        tag_check = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/tags/{cls.tag}^{{commit}}"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if tag_check.returncode == 0:
            resolved_tag = tag_check.stdout.strip()
            if resolved_tag != cls.commit:
                raise AssertionError(
                    f"{cls.tag} moved from frozen commit {cls.commit} to {resolved_tag}"
                )

        archive = subprocess.run(
            ["git", "archive", "--format=tar", cls.commit],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if archive.returncode != 0:
            raise AssertionError(archive.stderr.decode(errors="replace"))
        cls.archive_bytes = archive.stdout

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.tempdir.name)
        self.old_release = self.base / "teamwork-v3.4.2"
        self.old_release.mkdir()
        with tarfile.open(fileobj=io.BytesIO(self.archive_bytes), mode="r:") as value:
            value.extractall(self.old_release, filter="data")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_installer(
        self,
        checkout: pathlib.Path,
        home: pathlib.Path,
        target: str,
        *,
        configure_routing: bool = False,
        profile: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for name in (
            "TEAMWORK_INSTALL_MODE",
            "TEAMWORK_CODEX_PROFILE",
            "TEAMWORK_NOTIFICATIONS_ACTION",
            "TEAMWORK_CODEX_ROUTING",
        ):
            env.pop(name, None)
        env["HOME"] = str(home)
        env["CODEX_HOME"] = str(home / ".codex")
        home.mkdir(parents=True, exist_ok=True)
        args = ["bash", str(checkout / "install.sh")]
        if target != "cursor":
            args.append("--no-notifications")
        if target in {"codex", "all"} and not configure_routing:
            args.append("--no-codex-routing")
        if profile is not None:
            args.extend(("--profile", profile))
        args.append(target)
        return subprocess.run(
            args,
            cwd=checkout,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def run_check_update(
        self, home: pathlib.Path, *, readiness: bool = True
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["CODEX_HOME"] = str(home / ".codex")
        args = ["bash", str(REPO_ROOT / "scripts/check-update.sh")]
        if readiness:
            args.append("--readiness")
        args.append("--no-fetch")
        return subprocess.run(
            args,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def run_plugin_bootstrap_source(
        self, home: pathlib.Path, *, profile: str = "performance-first"
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["CODEX_HOME"] = str(home / ".codex")
        script = f"""
set -euo pipefail
ROOT={str(REPO_ROOT)!r}
source "$ROOT/scripts/install/common.sh"
source "$ROOT/scripts/install/policy.sh"
source "$ROOT/scripts/install/profiles.sh"
source "$ROOT/scripts/install/targets.sh"
teamwork_plugin_runtime_is_valid() {{ return 0; }}
CODEX_PROFILE={profile!r}
NOTIFICATIONS_ACTION=remove
CODEX_ROUTING_ACTION=configure
install_plugin_codex_bootstrap
"""
        return subprocess.run(
            ["bash", "-c", script],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def prepare_v342_activation_only(
        self, home: pathlib.Path, *, profile: str = "performance-first"
    ) -> pathlib.Path:
        old = self.run_installer(
            self.old_release,
            home,
            "codex",
            configure_routing=True,
            profile=profile,
        )
        self.assertEqual(old.returncode, 0, old.stdout)
        shutil.rmtree(home / ".agents/skills")
        activation = home / ".codex/teamwork/plugin-activation.json"
        activation.parent.mkdir(parents=True, exist_ok=True)
        activation.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "plugin": "teamwork-skill",
                    "marketplace": "teamwork",
                    "version": "3.4.2",
                    "profile": profile,
                    "notifications": "disabled",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        activation.chmod(0o600)
        return activation

    def install_v342(self, home: pathlib.Path, target: str) -> None:
        result = self.run_installer(self.old_release, home, target)
        self.assertEqual(result.returncode, 0, result.stdout)

    @staticmethod
    def tree_snapshot(
        root: pathlib.Path,
    ) -> dict[str, tuple[str, int, bytes | str]]:
        snapshot: dict[str, tuple[str, int, bytes | str]] = {}
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode & 0o7777
            if path.is_symlink():
                snapshot[rel] = ("symlink", mode, os.readlink(path))
            elif path.is_file():
                snapshot[rel] = ("file", mode, path.read_bytes())
            elif path.is_dir():
                snapshot[rel] = ("directory", mode, b"")
        return snapshot

    def assert_v4_skill_root(self, skill_root: pathlib.Path) -> None:
        self.assertEqual(
            {path.name for path in skill_root.iterdir() if path.is_dir()},
            EXPECTED_V4_SKILLS,
        )
        for skill in EXPECTED_V4_SKILLS:
            self.assertFalse((skill_root / skill).is_symlink(), skill_root / skill)
            skill_file = skill_root / skill / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill_file)
            self.assertIn(f"\nname: {skill}\n", skill_file.read_text(encoding="utf-8"))
        for retired in RETIRED_V342_SKILLS:
            self.assertFalse((skill_root / retired).exists(), skill_root / retired)
        actual_references = {
            path.relative_to(skill_root).as_posix()
            for path in skill_root.glob("*/references/*")
            if path.is_file()
        }
        self.assertEqual(actual_references, EXPECTED_V4_REFERENCES)
        self.assertEqual(
            (skill_root / ".teamwork-version").read_text(encoding="utf-8").strip(),
            (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        )

    def assert_v342_skill_root(self, skill_root: pathlib.Path) -> None:
        expected_files = {
            pathlib.PurePosixPath(value).relative_to("skills").as_posix()
            for value in self.fixture["files"]
        }
        actual_files = {
            path.relative_to(skill_root).as_posix()
            for path in skill_root.rglob("*")
            if path.is_file() and not path.name.startswith(".teamwork-")
        }
        self.assertEqual(actual_files, expected_files)
        self.assertEqual(
            (skill_root / ".teamwork-version").read_text(encoding="utf-8").strip(),
            "3.4.2",
        )
        for skill in {
            pathlib.PurePosixPath(value).parts[1]
            for value in self.fixture["files"]
        }:
            self.assertFalse((skill_root / skill).is_symlink(), skill_root / skill)

    def assert_v4_agent_roots(self, home: pathlib.Path) -> None:
        for platform, (relative, extension, expected) in PLATFORM_AGENT_ROOTS.items():
            with self.subTest(platform=platform):
                root = home / relative
                actual = {
                    path.stem for path in root.glob(f"*.{extension}") if path.is_file()
                }
                self.assertEqual(actual, expected)

    def assert_codex_profile_matrix(self, home: pathlib.Path, profile: str) -> None:
        root = home / ".codex/agents"
        for agent, (model, effort) in CODEX_PROFILE_MATRICES[profile].items():
            with self.subTest(profile=profile, agent=agent):
                rendered = (root / f"{agent}.toml").read_text(encoding="utf-8")
                self.assertIn(f'model = "{model}"', rendered)
                self.assertIn(
                    f'model_reasoning_effort = "{effort}"', rendered
                )

    def test_frozen_inventory_matches_the_pinned_release(self) -> None:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", self.commit, "--", "skills"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), self.fixture["files"])
        self.assertIn("skills/teamwork-execute/SKILL.md", self.fixture["files"])
        self.assertIn(
            "skills/using-teamwork/references/workflow-contract.md",
            self.fixture["files"],
        )
        self.assertNotIn("skills/teamwork-design/SKILL.md", self.fixture["files"])

    def test_real_copy_upgrade_reconciles_all_three_platforms(self) -> None:
        home = self.base / "upgrade-home"
        self.install_v342(home, "all")
        for relative in PLATFORM_SKILL_ROOTS.values():
            skill_root = home / relative
            self.assert_v342_skill_root(skill_root)
            self.assertFalse((skill_root / "teamwork-design").exists())

        upgraded = self.run_installer(
            REPO_ROOT, home, "all", configure_routing=True
        )
        self.assertEqual(upgraded.returncode, 0, upgraded.stdout)
        for relative in PLATFORM_SKILL_ROOTS.values():
            self.assert_v4_skill_root(home / relative)
        self.assert_v4_agent_roots(home)
        self.assert_codex_profile_matrix(home, "performance-first")

        readiness = self.run_check_update(home)
        self.assertEqual(readiness.returncode, 0, readiness.stdout)
        self.assertIn("INSTALL_READY=yes\n", readiness.stdout)
        self.assertNotRegex(
            readiness.stdout,
            r"(?m)^(?:CODEX|CURSOR|CLAUDE)_SKILL_CONTENT=.*(?:extra|drift)",
        )

    def test_cost_first_v342_upgrade_installs_exact_v4_surfaces(self) -> None:
        home = self.base / "cost-upgrade-home"
        old = self.run_installer(
            self.old_release, home, "all", profile="cost-first"
        )
        self.assertEqual(old.returncode, 0, old.stdout)
        upgraded = self.run_installer(
            REPO_ROOT,
            home,
            "all",
            configure_routing=True,
            profile="cost-first",
        )
        self.assertEqual(upgraded.returncode, 0, upgraded.stdout)
        for relative in PLATFORM_SKILL_ROOTS.values():
            self.assert_v4_skill_root(home / relative)
            self.assertEqual(
                (home / relative / ".teamwork-profile").read_text(encoding="utf-8").strip(),
                "cost-first",
            )
        self.assert_v4_agent_roots(home)
        self.assert_codex_profile_matrix(home, "cost-first")
        readiness = self.run_check_update(home)
        self.assertEqual(readiness.returncode, 0, readiness.stdout)
        self.assertIn("PROFILE=cost-first\n", readiness.stdout)

    def test_legacy_v342_profile_upgrades_to_the_v4_default(self) -> None:
        home = self.base / "legacy-profile-upgrade-home"
        old = self.run_installer(
            self.old_release, home, "all", profile="gpt56-role"
        )
        self.assertEqual(old.returncode, 0, old.stdout)
        upgraded = self.run_installer(
            REPO_ROOT, home, "all", configure_routing=True
        )
        self.assertEqual(upgraded.returncode, 0, upgraded.stdout)
        for relative in PLATFORM_SKILL_ROOTS.values():
            self.assertEqual(
                (home / relative / ".teamwork-profile").read_text(encoding="utf-8").strip(),
                "performance-first",
            )
        self.assert_v4_agent_roots(home)
        self.assert_codex_profile_matrix(home, "performance-first")

    def test_default_report_uses_v4_vocabulary_after_v342_upgrade(self) -> None:
        home = self.base / "report-after-upgrade-home"
        self.install_v342(home, "all")
        upgraded = self.run_installer(
            REPO_ROOT, home, "all", configure_routing=True
        )
        self.assertEqual(upgraded.returncode, 0, upgraded.stdout)

        report = self.run_check_update(home, readiness=False)
        output = report.stdout
        self.assertIn("Installed profile markers (derived): performance-first", output)
        self.assertIn("Cursor explorer model: gemini-3.5-flash", output)
        self.assertIn("Designer/Plan Reviewer=Sol/high, Reviewer=Sol/max", output)
        for retired_or_alias in (
            "explore.md",
            "Judge",
            "Deep",
            "gpt56-role",
        ):
            self.assertNotIn(retired_or_alias, output)

    def test_unknown_file_in_v342_retired_skill_fails_closed(self) -> None:
        for platform, relative in PLATFORM_SKILL_ROOTS.items():
            with self.subTest(platform=platform):
                home = self.base / f"unknown-{platform}"
                self.install_v342(home, platform)
                skill_root = home / relative
                user_file = skill_root / "using-teamwork/user-notes.md"
                user_file.write_text("preserve this user file\n", encoding="utf-8")
                before = self.tree_snapshot(home)

                result = self.run_installer(REPO_ROOT, home, platform)

                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("unknown", result.stdout.lower())
                self.assertEqual(self.tree_snapshot(home), before)
                self.assertEqual(
                    user_file.read_text(encoding="utf-8"),
                    "preserve this user file\n",
                )
                self.assertFalse((skill_root / "teamwork-design").exists())

    def test_modified_v342_agent_fails_before_any_upgrade_write(self) -> None:
        for platform, relative in PLATFORM_SKILL_ROOTS.items():
            with self.subTest(platform=platform):
                home = self.base / f"modified-agent-{platform}"
                self.install_v342(home, platform)
                agent_root = home / PLATFORM_AGENT_ROOTS[platform][0]
                agent_file = agent_root / RETIRED_AGENT_SAMPLE[platform]
                agent_file.write_text(
                    agent_file.read_text(encoding="utf-8") + "\nuser change\n",
                    encoding="utf-8",
                )
                before = self.tree_snapshot(home)
                result = self.run_installer(REPO_ROOT, home, platform)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("Modified v3.4.2", result.stdout)
                self.assertEqual(self.tree_snapshot(home), before)

    def test_marketplace_v342_activation_only_bootstrap_migrates_frozen_agents(self) -> None:
        home = self.base / "activation-only"
        activation = self.prepare_v342_activation_only(home)
        self.assertFalse((home / ".agents/skills/.teamwork-version").exists())
        self.assertEqual(
            len(list((home / ".codex/agents").glob("teamwork-*.toml"))), 7
        )

        result = self.run_plugin_bootstrap_source(home)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(
            {path.stem for path in (home / ".codex/agents").glob("*.toml")},
            PLATFORM_AGENT_ROOTS["codex"][2],
        )
        self.assert_codex_profile_matrix(home, "performance-first")
        self.assertFalse((home / ".agents/skills").exists())
        current_version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertIn(
            f'"version": "{current_version}"',
            activation.read_text(encoding="utf-8"),
        )
        self.assertTrue((home / ".codex/config.toml").is_file())
        self.assertIn(
            "<!-- TEAMWORK_CODEX_GLOBAL_START -->",
            (home / ".codex/AGENTS.md").read_text(encoding="utf-8"),
        )

    def test_marketplace_v342_activation_only_preflight_failures_are_byte_atomic(self) -> None:
        cases = (
            "agent-byte",
            "missing-profile",
            "wrong-profile-type",
            "inconsistent-profile",
            "unmanaged-v4-agent",
        )
        for case in cases:
            with self.subTest(case=case):
                home = self.base / f"activation-only-{case}"
                activation = self.prepare_v342_activation_only(home)
                if case == "agent-byte":
                    agent = home / ".codex/agents/teamwork-explorer.toml"
                    agent.write_bytes(agent.read_bytes() + b"x")
                elif case == "unmanaged-v4-agent":
                    (home / ".codex/agents/teamwork-researcher.toml").write_text(
                        'name = "teamwork_researcher"\nuser_owned = true\n',
                        encoding="utf-8",
                    )
                else:
                    marker = json.loads(activation.read_text(encoding="utf-8"))
                    if case == "missing-profile":
                        marker.pop("profile")
                    elif case == "wrong-profile-type":
                        marker["profile"] = ["performance-first"]
                    else:
                        marker["profile"] = "cost-first"
                    activation.write_text(
                        json.dumps(marker, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                self.assertTrue((home / ".codex/config.toml").is_file())
                self.assertTrue((home / ".codex/AGENTS.md").is_file())
                self.assertTrue((home / ".codex/agents").is_dir())
                self.assertTrue(activation.is_file())
                before = self.tree_snapshot(home)

                result = self.run_plugin_bootstrap_source(home)

                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(self.tree_snapshot(home), before)

    def test_modified_v342_managed_policy_fails_before_upgrade_write(self) -> None:
        policies = {
            "codex": pathlib.Path(".codex/AGENTS.md"),
            "claude": pathlib.Path(".claude/CLAUDE.md"),
        }
        for platform, relative in policies.items():
            with self.subTest(platform=platform):
                home = self.base / f"modified-policy-{platform}"
                self.install_v342(home, platform)
                policy = home / relative
                original = policy.read_text(encoding="utf-8")
                self.assertIn("Work within the user's request", original)
                policy.write_text(
                    original.replace(
                        "Work within the user's request",
                        "Changed within the user's request",
                        1,
                    ),
                    encoding="utf-8",
                )
                before = self.tree_snapshot(home)
                result = self.run_installer(REPO_ROOT, home, platform)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("Modified v3.4.2", result.stdout)
                self.assertEqual(self.tree_snapshot(home), before)

    def test_freshness_rejects_extra_retired_owned_content(self) -> None:
        home = self.base / "freshness-home"
        installed = self.run_installer(
            REPO_ROOT, home, "all", configure_routing=True
        )
        self.assertEqual(installed.returncode, 0, installed.stdout)

        clean = self.run_check_update(home)
        self.assertEqual(clean.returncode, 0, clean.stdout)
        self.assertIn("INSTALL_READY=yes\n", clean.stdout)

        old_using = self.old_release / "skills/using-teamwork"
        expected_missing_keys = {
            "codex": "codex-skill-content",
            "cursor": "cursor-skill-content",
            "claude": "claude-skill-content",
        }
        for platform, relative in PLATFORM_SKILL_ROOTS.items():
            with self.subTest(platform=platform):
                retired_copy = home / relative / "using-teamwork"
                shutil.copytree(old_using, retired_copy)
                stale = self.run_check_update(home)
                self.assertNotEqual(stale.returncode, 0, stale.stdout)
                self.assertIn("INSTALL_READY=no\n", stale.stdout)
                self.assertIn(expected_missing_keys[platform], stale.stdout)
                shutil.rmtree(retired_copy)

        clean_again = self.run_check_update(home)
        self.assertEqual(clean_again.returncode, 0, clean_again.stdout)
        self.assertIn("INSTALL_READY=yes\n", clean_again.stdout)

        worker = home / ".codex/agents/teamwork-worker.toml"
        worker.write_text(
            worker.read_text(encoding="utf-8").replace(
                'model_reasoning_effort = "high"',
                'model_reasoning_effort = "medium"',
                1,
            ),
            encoding="utf-8",
        )
        wrong_codex_matrix = self.run_check_update(home)
        self.assertNotEqual(wrong_codex_matrix.returncode, 0, wrong_codex_matrix.stdout)
        self.assertIn("codex-agent-content", wrong_codex_matrix.stdout)
        worker.write_text(
            worker.read_text(encoding="utf-8").replace(
                'model_reasoning_effort = "medium"',
                'model_reasoning_effort = "high"',
                1,
            ),
            encoding="utf-8",
        )

        cursor_profile = home / PLATFORM_SKILL_ROOTS["cursor"] / ".teamwork-profile"
        cursor_profile.write_text("cost-first\n", encoding="utf-8")
        wrong_profile = self.run_check_update(home)
        self.assertNotEqual(wrong_profile.returncode, 0, wrong_profile.stdout)
        self.assertIn("INSTALL_READY=no\n", wrong_profile.stdout)
        self.assertIn("profile", wrong_profile.stdout)
        cursor_profile.write_text("performance-first\n", encoding="utf-8")

        expected_agent_keys = {
            "codex": "codex-agent-content",
            "cursor": "cursor-agent-content",
            "claude": "claude-agent-content",
        }
        for platform, (relative, _, _) in PLATFORM_AGENT_ROOTS.items():
            with self.subTest(platform=f"retired-agent-{platform}"):
                retired = home / relative / RETIRED_AGENT_SAMPLE[platform]
                retired.write_text("retired Teamwork role\n", encoding="utf-8")
                stale = self.run_check_update(home)
                self.assertNotEqual(stale.returncode, 0, stale.stdout)
                self.assertIn("INSTALL_READY=no\n", stale.stdout)
                self.assertIn(expected_agent_keys[platform], stale.stdout)
                retired.unlink()


if __name__ == "__main__":
    unittest.main()
