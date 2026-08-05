"""Contracts for manifest-owned Teamwork agent templates and host profiles."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import tomllib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from teamwork_tooling.topology import host_role_paths  # noqa: E402


PERFORMANCE = {
    "codex": {
        "researcher": ("gpt-5.6-terra", "high"),
        "explorer": ("gpt-5.6-terra", "high"),
        "debugger": ("gpt-5.6-sol", "high"),
        "challenger": ("gpt-5.6-sol", "high"),
        "planner": ("gpt-5.6-sol", "high"),
        "worker": ("gpt-5.6-terra", "high"),
        "writer": ("gpt-5.6-luna", "high"),
        "reviewer": ("gpt-5.6-sol", "max"),
    },
    "claude": {
        "researcher": ("sonnet", "medium"),
        "explorer": ("sonnet", "medium"),
        "debugger": ("opus", "high"),
        "challenger": ("opus", "high"),
        "planner": ("opus", "high"),
        "worker": ("sonnet", "medium"),
        "writer": ("haiku", "medium"),
        "reviewer": ("opus", "max"),
    },
    "cursor": {
        "researcher": ("gpt-5.6-terra-medium",),
        "explorer": ("gemini-3.5-flash",),
        "debugger": ("claude-opus-4-8-thinking-high",),
        "challenger": ("gpt-5.6-sol-medium",),
        "planner": ("gpt-5.6-terra-medium",),
        "worker": ("composer-2.5-fast",),
        "writer": ("composer-2.5-fast",),
        "reviewer": ("claude-fable-5-thinking-high",),
    },
}

COST = {
    "codex": {
        **PERFORMANCE["codex"],
        "researcher": ("gpt-5.6-terra", "high"),
        "explorer": ("gpt-5.6-luna", "high"),
        "debugger": ("gpt-5.6-terra", "high"),
        "challenger": ("gpt-5.6-terra", "high"),
        "planner": ("gpt-5.6-terra", "high"),
        "worker": ("gpt-5.6-luna", "xhigh"),
        "writer": ("gpt-5.6-luna", "high"),
        "reviewer": ("gpt-5.6-sol", "high"),
    },
    "claude": {
        **PERFORMANCE["claude"],
        "researcher": ("haiku", "medium"),
        "explorer": ("haiku", "medium"),
        "worker": ("haiku", "medium"),
    },
    "cursor": {
        **PERFORMANCE["cursor"],
        "researcher": ("gemini-3.5-flash",),
        "explorer": ("gemini-3.5-flash",),
        "debugger": ("gpt-5.6-terra-medium",),
        "challenger": ("gpt-5.6-terra-medium",),
        "planner": ("gpt-5.6-luna-medium",),
        "reviewer": ("claude-opus-4-8-thinking-high",),
    },
}


def markdown_frontmatter(path: pathlib.Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    end = lines.index("---", 1)
    return dict(line.split(":", 1) for line in lines[1:end])


def profile_value(platform: str, profile: str, role: str) -> tuple[str, ...]:
    agent = f"teamwork-{role}" if platform == "codex" else role
    function = f"{platform}_agent_profile_values"
    command = (
        f'ROOT="$1"; source "$1/scripts/install/common.sh"; '
        f'source "$1/scripts/install/profiles.sh"; CODEX_PROFILE="$2"; '
        f'{function} "$3"'
    )
    result = subprocess.run(
        ["bash", "-c", command, "profiles", str(ROOT), profile, agent],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(result.stdout.split())


class RoleProfileTests(unittest.TestCase):
    def test_manifest_templates_exist_and_match_host_identity(self) -> None:
        topology = host_role_paths(ROOT)
        self.assertEqual(set(topology), {"codex", "cursor", "claude"})
        for host, roles in topology.items():
            self.assertEqual(set(roles), set(PERFORMANCE[host]))
            for role, relative in roles.items():
                path = ROOT / relative
                self.assertTrue(path.is_file(), path)
                if host == "codex":
                    data = tomllib.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(data["name"], f"teamwork_{role}")
                    self.assertEqual(
                        (data["model"], data["model_reasoning_effort"]),
                        PERFORMANCE[host][role],
                    )
                else:
                    data = {key.strip(): value.strip() for key, value in markdown_frontmatter(path).items()}
                    self.assertEqual(data["name"], role)
                    self.assertEqual((data["model"],), PERFORMANCE[host][role][:1])

    def test_profile_functions_cover_manifest_roles_without_fallback(self) -> None:
        for profile, expected in (("performance-first", PERFORMANCE), ("cost-first", COST)):
            for host, roles in expected.items():
                for role, value in roles.items():
                    with self.subTest(profile=profile, host=host, role=role):
                        self.assertEqual(profile_value(host, profile, role), value)

    def test_agent_methods_preserve_the_new_boundaries(self) -> None:
        texts = {
            role: "\n".join((ROOT / relative).read_text(encoding="utf-8") for relative in paths.values())
            for role, paths in {
                role: {host: roles[role] for host, roles in host_role_paths(ROOT).items()}
                for role in PERFORMANCE["codex"]
            }.items()
        }
        self.assertIn("3–5 plausible hypotheses", texts["debugger"])
        self.assertIn("Structured logging is optional", texts["debugger"])
        self.assertIn("Do not design", texts["challenger"])
        self.assertIn("clear or selected direction", texts["planner"])
        self.assertIn("plan", texts["reviewer"].lower())
        self.assertIn("preserve unrelated", texts["worker"])
        self.assertIn("one reader-first live document", texts["writer"])
        for text in texts.values():
            self.assertNotIn("Plan Reviewer", text)
            self.assertNotIn("Teamwork Designer", text)
            self.assertNotIn("case-inspect", text)

    def test_retired_cleanup_removes_recognized_files_and_preserves_unknown_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            recognized = root / "designer.md"
            recognized.write_text("name: designer\nYou are the Teamwork Designer.\n", encoding="utf-8")
            unknown = root / "plan-reviewer.md"
            unknown.write_text("personal file\n", encoding="utf-8")
            command = (
                'ROOT="$1"; source "$1/scripts/install/common.sh"; '
                'source "$1/scripts/install/profiles.sh"; '
                'remove_retired_agent_files cursor "$2" designer plan-reviewer'
            )
            subprocess.run(
                ["bash", "-c", command, "cleanup", str(ROOT), str(root)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertFalse(recognized.exists())
            self.assertTrue(unknown.exists())

    def test_codex_retired_designer_cleanup_requires_official_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            custom = root / "teamwork-designer.toml"
            custom.write_text(
                'name = "teamwork_designer"\n'
                'developer_instructions = "You are the Teamwork Designer. custom"\n',
                encoding="utf-8",
            )
            command = (
                'ROOT="$1"; source "$1/scripts/install/common.sh"; '
                'source "$1/scripts/install/profiles.sh"; '
                'remove_retired_agent_files codex "$2" teamwork-designer'
            )
            subprocess.run(
                ["bash", "-c", command, "cleanup", str(ROOT), str(root)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(custom.exists())


if __name__ == "__main__":
    unittest.main()
