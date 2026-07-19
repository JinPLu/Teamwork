"""Focused contracts for the v4 eight-role templates and profile adapters."""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import tomllib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
ROLE_SLUGS = (
    "researcher",
    "explorer",
    "debugger",
    "designer",
    "planner",
    "worker",
    "plan-reviewer",
    "reviewer",
)

PERFORMANCE = {
    "codex": {
        "researcher": ("gpt-5.5", "high"),
        "explorer": ("gpt-5.5", "high"),
        "debugger": ("gpt-5.5", "high"),
        "designer": ("gpt-5.6-sol", "high"),
        "planner": ("gpt-5.5", "high"),
        "worker": ("gpt-5.5", "high"),
        "plan-reviewer": ("gpt-5.6-sol", "high"),
        "reviewer": ("gpt-5.6-sol", "max"),
    },
    "claude": {
        "researcher": ("sonnet", "medium"),
        "explorer": ("sonnet", "medium"),
        "debugger": ("opus", "high"),
        "designer": ("opus", "high"),
        "planner": ("opus", "high"),
        "worker": ("sonnet", "medium"),
        "plan-reviewer": ("opus", "max"),
        "reviewer": ("opus", "max"),
    },
    "cursor": {
        "researcher": ("claude-sonnet-4-6",),
        "explorer": ("claude-sonnet-4-6",),
        "debugger": ("claude-opus-4-8-thinking-high",),
        "designer": ("claude-opus-4-8-thinking-high",),
        "planner": ("claude-opus-4-8-thinking-high",),
        "worker": ("composer-2.5-fast",),
        "plan-reviewer": ("claude-opus-4-8-thinking-high",),
        "reviewer": ("claude-opus-4-8-thinking-high",),
    },
}

COST = {
    "codex": {
        **PERFORMANCE["codex"],
        "researcher": ("gpt-5.5", "medium"),
        "explorer": ("gpt-5.5", "medium"),
        "worker": ("gpt-5.5", "medium"),
        "debugger": ("gpt-5.5", "medium"),
        "designer": ("gpt-5.6-sol", "medium"),
        "planner": ("gpt-5.5", "medium"),
        "plan-reviewer": ("gpt-5.6-sol", "high"),
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
        "researcher": ("composer-2.5",),
        "explorer": ("composer-2.5",),
        "worker": ("composer-2.5",),
    },
}


def frontmatter(path: pathlib.Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    values = {}
    for line in lines[1:end]:
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


class RoleProfilesV4Test(unittest.TestCase):
    def test_exact_eight_role_inventory_and_host_schema(self) -> None:
        expected = {
            "codex-agents": {f"teamwork-{role}.toml" for role in ROLE_SLUGS},
            "cursor-agents": {f"{role}.md" for role in ROLE_SLUGS},
            "claude-agents": {f"{role}.md" for role in ROLE_SLUGS},
        }
        for directory, names in expected.items():
            actual = {path.name for path in (ROOT / "templates" / directory).iterdir() if path.is_file()}
            self.assertEqual(names, actual, directory)

        for role in ROLE_SLUGS:
            codex = tomllib.loads(
                (ROOT / "templates/codex-agents" / f"teamwork-{role}.toml").read_text(encoding="utf-8")
            )
            self.assertEqual(f"teamwork_{role.replace('-', '_')}", codex["name"])
            self.assertEqual(PERFORMANCE["codex"][role], (codex["model"], codex["model_reasoning_effort"]))
            self.assertIn(codex["sandbox_mode"], {"read-only", "workspace-write"})
            for host in ("cursor-agents", "claude-agents"):
                data = frontmatter(ROOT / "templates" / host / f"{role}.md")
                self.assertEqual(role, data["name"])
                self.assertIn("model", data)

    def test_leaf_scope_write_and_acceptance_boundaries(self) -> None:
        for directory in ("codex-agents", "cursor-agents", "claude-agents"):
            for path in (ROOT / "templates" / directory).iterdir():
                text = path.read_text(encoding="utf-8")
                normalized = " ".join(text.split())
                for phrase in (
                    "Mission:", "Owned scope:", "Input:", "Output:", "Verify:", "Stop:",
                    "Do not spawn", "Do not interact with the user", "Do not own the global task",
                    "Do not expand scope", "Do not self-accept",
                ):
                    self.assertIn(phrase, normalized, f"{path}: {phrase}")

        for role in ("designer", "plan-reviewer", "reviewer"):
            codex = tomllib.loads(
                (ROOT / "templates/codex-agents" / f"teamwork-{role}.toml").read_text(encoding="utf-8")
            )
            self.assertEqual("read-only", codex["sandbox_mode"])
            for host in ("cursor-agents", "claude-agents"):
                text = (ROOT / "templates" / host / f"{role}.md").read_text(encoding="utf-8")
                self.assertIn("strictly read-only", text)

        planner_text = "\n".join(
            (ROOT / "templates" / host / "planner.md").read_text(encoding="utf-8")
            for host in ("cursor-agents", "claude-agents")
        )
        self.assertIn("single exact Plan path", planner_text)
        worker_text = (ROOT / "templates/codex-agents/teamwork-worker.toml").read_text(encoding="utf-8")
        for phrase in ("canonical owner", "smallest complete", "proportional", "real path", "residue"):
            self.assertIn(phrase, worker_text)

    def test_proportional_routing_boundaries_are_consistent_across_hosts(self) -> None:
        role_clauses = {
            "designer": ("only the evidence tracks that Root conditionally supplies",),
            "planner": ("execution-ready", "user request or named material risk gate"),
            "worker": ("self-verifies its slice", "does not trigger Review itself"),
            "plan-reviewer": ("user request or named material risk gate", "at most one bounded delta recheck"),
            "reviewer": ("sealed integrated candidate", "one repair batch", "at most one bounded delta recheck per candidate"),
        }
        for host in ("codex-agents", "cursor-agents", "claude-agents"):
            for role, clauses in role_clauses.items():
                prefix = "teamwork-" if host == "codex-agents" else ""
                suffix = ".toml" if host == "codex-agents" else ".md"
                text = (ROOT / "templates" / host / f"{prefix}{role}{suffix}").read_text(encoding="utf-8")
                normalized = " ".join(text.split())
                for clause in clauses:
                    self.assertIn(clause, normalized, f"{host}/{role}: {clause}")

    def test_profile_matrix_is_exact_and_unknowns_fail_closed(self) -> None:
        for profile, matrix in (("performance-first", PERFORMANCE), ("cost-first", COST)):
            for host, roles in matrix.items():
                function = f"{host}_agent_profile_values"
                for role, expected in roles.items():
                    agent = f"teamwork-{role}" if host == "codex" else role
                    command = (
                        f"set -euo pipefail; source scripts/install/profiles.sh; "
                        f"CODEX_PROFILE={profile}; {function} {agent}"
                    )
                    result = subprocess.run(
                        ["bash", "-c", command], cwd=ROOT, text=True, capture_output=True, check=False
                    )
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(expected, tuple(result.stdout.split()))

        for command in (
            "CODEX_PROFILE=performance-first; codex_agent_profile_values teamwork-deep-reviewer",
            "CODEX_PROFILE=unknown; claude_agent_profile_values reviewer",
            "CODEX_PROFILE=cost-first; cursor_agent_profile_values judge",
        ):
            result = subprocess.run(
                ["bash", "-c", f"source scripts/install/profiles.sh; {command}"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(0, result.returncode, command)
            self.assertIn("unsupported", result.stderr.lower())

    def test_install_adapter_rejects_missing_schema_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary) / "invalid.toml"
            destination = pathlib.Path(temporary) / "out.toml"
            source.write_text(
                'name = "teamwork_worker"\nmodel = "gpt-5.6-sol"\n'
                'sandbox_mode = "workspace-write"\n',
                encoding="utf-8",
            )
            command = (
                "set -euo pipefail; source scripts/install/profiles.sh; "
                "CODEX_PROFILE=performance-first; INSTALL_MODE=copy; "
                f"install_codex_agent_file {source!s} {destination!s} teamwork-worker"
            )
            result = subprocess.run(
                ["bash", "-c", command], cwd=ROOT, text=True, capture_output=True, check=False
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("invalid codex effort profile field", result.stderr.lower())
            self.assertFalse(destination.exists())

    def test_codex_adapter_rejects_noncanonical_source_effort(self) -> None:
        canonical = (ROOT / "templates/codex-agents/teamwork-worker.toml").read_text(encoding="utf-8")
        for invalid_effort in ("medium", "max"):
            with self.subTest(effort=invalid_effort), tempfile.TemporaryDirectory() as temporary:
                source = pathlib.Path(temporary) / "teamwork-worker.toml"
                destination = pathlib.Path(temporary) / "out.toml"
                source.write_text(
                    canonical.replace(
                        'model_reasoning_effort = "high"',
                        f'model_reasoning_effort = "{invalid_effort}"',
                        1,
                    ),
                    encoding="utf-8",
                )
                command = (
                    "set -euo pipefail; source scripts/install/profiles.sh; "
                    "CODEX_PROFILE=cost-first; INSTALL_MODE=copy; "
                    f"install_codex_agent_file {source!s} {destination!s} teamwork-worker"
                )
                result = subprocess.run(
                    ["bash", "-c", command], cwd=ROOT, text=True,
                    capture_output=True, check=False,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn("canonical performance mapping", result.stderr.lower())
                self.assertFalse(destination.exists())

    def test_adapters_render_every_role_in_both_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_root = pathlib.Path(temporary)
            for profile, matrix in (("performance-first", PERFORMANCE), ("cost-first", COST)):
                for host, roles in matrix.items():
                    function = f"install_{host}_agent_file"
                    for role, expected in roles.items():
                        agent = f"teamwork-{role}" if host == "codex" else role
                        extension = "toml" if host == "codex" else "md"
                        source = ROOT / "templates" / f"{host}-agents" / f"{agent}.{extension}"
                        destination = output_root / profile / host / f"{agent}.{extension}"
                        command = (
                            "set -euo pipefail; source scripts/install/profiles.sh; "
                            f"CODEX_PROFILE={profile}; INSTALL_MODE=copy; "
                            f"{function} {source!s} {destination!s} {agent}; "
                            + (
                                f"teamwork_codex_agent_file_is_recognized {destination!s} {agent}"
                                if host == "codex" else ":"
                            )
                        )
                        result = subprocess.run(
                            ["bash", "-c", command], cwd=ROOT, text=True,
                            capture_output=True, check=False,
                        )
                        self.assertEqual(0, result.returncode, result.stderr)
                        if host == "codex":
                            data = tomllib.loads(destination.read_text(encoding="utf-8"))
                            actual = (data["model"], data["model_reasoning_effort"])
                        else:
                            data = frontmatter(destination)
                            actual = (data["model"],) if host == "cursor" else (data["model"], data["effort"])
                        self.assertEqual(expected, actual, f"{profile}:{host}:{role}")


if __name__ == "__main__":
    unittest.main()
