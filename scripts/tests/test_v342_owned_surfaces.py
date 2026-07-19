#!/usr/bin/env python3
"""Prove the complete v3.4.2 migration inventory from its real producers."""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
COMMIT = "93572a3e8029b5348ee31d2a65b0c9a06b45beed"
PROFILES = (
    "performance-first", "cost-first", "gpt56-role", "gpt56-high",
    "gpt56-xhigh", "gpt55-high", "gpt55-xhigh",
)
EXPECTED_RUNTIME_SURFACES = {
    "~/.agents/skills/{skill}/**": ("installed-skill", "W3-installer", "directory", "exact frozen owned inventory bytes plus .teamwork-version/.teamwork-profile; unknown files fail closed"),
    "~/.cursor/skills/{skill}/**": ("installed-skill", "W3-installer", "directory", "exact frozen owned inventory bytes plus .teamwork-version/.teamwork-profile; unknown files fail closed"),
    "~/.claude/skills/{skill}/**": ("installed-skill", "W3-installer", "directory", "exact frozen owned inventory bytes plus .teamwork-version/.teamwork-profile; unknown files fail closed"),
    "~/.codex/agents/teamwork-*.toml": ("installed-agent", "W3-roles", "file", "recognized Teamwork name plus selected profile model/effort or frozen symlink target"),
    "~/.cursor/agents/*.md": ("installed-agent", "W3-roles", "file", "recognized Teamwork agent frontmatter plus selected profile model or frozen symlink target"),
    "~/.claude/agents/*.md": ("installed-agent", "W3-roles", "file", "recognized Teamwork agent frontmatter plus selected profile model/effort or frozen symlink target"),
    "~/.codex/config.toml": ("codex-routing", "W3-installer", "file", "Teamwork-managed routing block with unrelated TOML preserved"),
    "~/.codex/hooks.json": ("codex-notification", "W3-installer", "file", "Teamwork-owned notification hook entries with unrelated hooks preserved"),
    "~/.codex/teamwork/notify.py": ("notification-runtime", "W3-installer", "file", "exact Teamwork notifier or recognized owned link target"),
    "~/.claude/settings.json": ("claude-notification", "W3-installer", "file", "Teamwork-owned notification hook entries with unrelated settings preserved"),
    "~/.claude/teamwork/notify.py": ("notification-runtime", "W3-installer", "file", "exact Teamwork notifier or recognized owned link target"),
    "~/.codex/teamwork/plugin-activation.json": ("plugin-activation", "W3-installer", "file", "plugin activation schema_version 1 with Teamwork plugin/marketplace/profile/notification fields"),
    "docs/teamwork/index.json": ("runtime-artifact", "W5-init", "file", "Teamwork index schema_version 1 with user-owned entries preserved"),
    "docs/teamwork/README.md": ("runtime-artifact", "W5-init", "file", "managed routing anchors with user content preserved"),
    "docs/teamwork/current.md": ("runtime-artifact", "W5-init", "file", "active-state anchors with user content preserved"),
    "docs/teamwork/discussion/*.md": ("runtime-artifact", "W4-artifacts", "file", "discussion schema_version 1 or accepted legacy migration grammar"),
    "docs/teamwork/research/**": ("runtime-artifact", "ROOT-RUNTIME", "directory", "ignored runtime artifact namespace; exact preflight tree snapshot and user ownership preserved"),
    "docs/teamwork/design/**": ("runtime-artifact", "ROOT-RUNTIME", "directory", "ignored runtime artifact namespace; exact preflight tree snapshot and user ownership preserved"),
    "docs/teamwork/plans/**": ("runtime-artifact", "ROOT-RUNTIME", "directory", "ignored runtime artifact namespace; exact preflight tree snapshot and user ownership preserved"),
    "docs/teamwork/reports/**": ("runtime-artifact", "ROOT-RUNTIME", "directory", "ignored runtime artifact namespace; exact preflight tree snapshot and user ownership preserved"),
    "docs/teamwork/workflows/**": ("runtime-artifact", "ROOT-RUNTIME", "directory", "ignored runtime artifact namespace; exact preflight tree snapshot and user ownership preserved"),
    "AGENTS.md#TEAMWORK_PROJECT": ("managed-project-policy", "W5-init", "managed-block", "single TEAMWORK_PROJECT_START/END block"),
    ".gitignore#TEAMWORK_LOCAL": ("managed-project-policy", "W5-init", "managed-block", "single TEAMWORK_LOCAL_START/END block"),
}
PROFILE_AGENTS = {
    "codex": ("codex_agent_profile_values", ("teamwork-explorer", "teamwork-worker", "teamwork-designer", "teamwork-judge", "teamwork-reviewer", "teamwork-deep-judge", "teamwork-deep-reviewer"), "templates/codex-agents/", ".toml"),
    "cursor": ("cursor_agent_profile_values", ("explore", "worker", "designer", "judge", "code-reviewer", "deep-judge", "deep-reviewer"), "templates/cursor-agents/", ".md"),
    "claude": ("claude_agent_profile_values", ("explore", "worker", "designer", "judge", "code-reviewer", "deep-judge", "deep-reviewer"), "templates/claude-agents/", ".md"),
}


def git(*args: str, binary: bool = False):
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, check=False,
        text=not binary,
    )
    if result.returncode:
        error = result.stderr if isinstance(result.stderr, str) else result.stderr.decode()
        raise AssertionError(error)
    return result.stdout


def copy_items() -> tuple[tuple[str, str], ...]:
    module = ast.parse(git("show", f"{COMMIT}:scripts/build-codex-plugin.py"))
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "COPY_ITEMS"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            return tuple((str(source), str(destination)) for source, destination in value)
    raise AssertionError("v3.4.2 build producer has no COPY_ITEMS")


def published_paths() -> set[str]:
    """Derive owned bytes from the published bundle/install producers, not a list."""
    all_paths = set(git("ls-tree", "-r", "--name-only", COMMIT).splitlines())
    result: set[str] = set()
    for source, _destination in copy_items():
        prefix = f"{source.rstrip('/')}/"
        if any(path.startswith(prefix) for path in all_paths):
            result.update(path for path in all_paths if path.startswith(prefix))
        else:
            self_path = source.rstrip("/")
            if self_path not in all_paths:
                raise AssertionError(f"COPY_ITEMS source missing from published tree: {source}")
            result.add(self_path)
    # These are published producers/manifests outside the Codex bundle copy list.
    result.update(path for path in all_paths if path.startswith((
        ".agents/plugins/", ".claude-plugin/", "hooks/", "plugins/teamwork-skill/", "scripts/validation/",
    )))
    result.update({"scripts/build-codex-plugin.py", "scripts/validate.sh"})
    # The three-host source templates are migration authority even where the
    # Codex marketplace bundle only copies the Codex host projection.
    result.update(path for path in all_paths if path.startswith((
        "templates/cursor-agents/", "templates/claude-agents/",
    )))
    return result


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class V342OwnedSurfacesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(
            (FIXTURES / "v3.4.2-owned-surfaces.json").read_text(encoding="utf-8")
        )

    def test_deterministic_inventory_reproduces_every_published_producer_byte(self) -> None:
        self.assertEqual(self.fixture["schema_version"], 1)
        self.assertEqual(self.fixture["commit"], COMMIT)
        deterministic = self.fixture["deterministic_surfaces"]
        self.assertEqual(len(deterministic), len({entry["path"] for entry in deterministic}))
        tracked = {
            entry["path"]: entry
            for entry in deterministic
            if not entry["path"].startswith("managed://")
        }
        self.assertEqual(set(tracked), published_paths())
        self.assertIn("hooks/hooks.json", tracked)
        for path, entry in tracked.items():
            fields = git("ls-tree", COMMIT, "--", path).strip().split()
            self.assertGreaterEqual(len(fields), 3, path)
            mode, object_type, oid = fields[:3]
            self.assertEqual(object_type, "blob", path)
            blob = git("cat-file", "blob", oid, binary=True)
            self.assertEqual(entry["file_type"], "symlink" if mode == "120000" else "file", path)
            self.assertEqual(
                entry["mode"],
                "0777" if mode == "120000" else ("0755" if mode == "100755" else "0644"),
                path,
            )
            self.assertEqual(entry["sha256"], sha256(blob), path)

    def test_managed_policy_blocks_reproduce_published_bytes(self) -> None:
        policy_source = git("show", f"{COMMIT}:scripts/install/policy.sh")
        with tempfile.TemporaryDirectory() as directory:
            script = pathlib.Path(directory) / "policy.sh"
            script.write_text(policy_source, encoding="utf-8")
            policies = [
                entry for entry in self.fixture["deterministic_surfaces"]
                if entry["surface_class"] == "managed-policy"
            ]
            expected = {
                ("managed://codex/global-policy", "write_teamwork_codex_global_policy", "${CODEX_HOME:-~/.codex}/AGENTS.md"),
                ("managed://cursor/global-policy", "write_teamwork_cursor_global_policy", "Cursor Settings/User Rules"),
                ("managed://claude/global-policy", "write_teamwork_claude_global_policy", "~/.claude/CLAUDE.md"),
            }
            self.assertEqual(
                {(entry["path"], entry["producer"], entry["managed_path_pattern"]) for entry in policies},
                expected,
            )
            self.assertEqual(len(policies), len(expected))
            for entry in policies:
                result = subprocess.run(
                    ["bash", "-c", 'source "$1"; "$2"', "bash", str(script), entry["producer"]],
                    capture_output=True, check=True,
                )
                self.assertEqual(entry["file_type"], "managed-block")
                self.assertEqual(entry["mode"], "0644")
                self.assertEqual(entry["sha256"], sha256(result.stdout))

    def test_profile_rendered_agents_reproduce_published_bytes(self) -> None:
        profile_source = git("show", f"{COMMIT}:scripts/install/profiles.sh")
        with tempfile.TemporaryDirectory() as directory:
            script = pathlib.Path(directory) / "profiles.sh"
            script.write_text(profile_source, encoding="utf-8")
            rows = [
                entry for entry in self.fixture["deterministic_surfaces"]
                if entry["surface_class"] == "profile-rendered-agent"
            ]
            self.assertEqual(len(rows), len(PROFILES) * 3 * 7)
            expected_combinations = {
                (host, profile, agent, prefix + agent + suffix, function)
                for host, (function, agents, prefix, suffix) in PROFILE_AGENTS.items()
                for profile in PROFILES
                for agent in agents
            }
            actual_combinations = {
                (entry["host"], entry["profile"], entry["agent"], entry["source_path"], entry["profile_function"])
                for entry in rows
            }
            self.assertEqual(actual_combinations, expected_combinations)
            self.assertEqual(len(rows), len(actual_combinations))
            for entry in rows:
                source = git("cat-file", "blob", f"{COMMIT}:{entry['source_path']}", binary=True).decode()
                values = subprocess.run(
                    ["bash", "-c", 'source "$1"; CODEX_PROFILE="$2"; "$3" "$4"',
                     "bash", str(script), entry["profile"], entry["profile_function"], entry["agent"]],
                    text=True, capture_output=True, check=True,
                ).stdout.split()
                if entry["host"] == "codex":
                    source = re.sub(r"(?m)^model = .*$", f'model = "{values[0]}"', source)
                    source = re.sub(r"(?m)^model_reasoning_effort = .*$", f'model_reasoning_effort = "{values[1]}"', source)
                elif entry["host"] == "claude":
                    source = re.sub(r"(?m)^model: .*$", f"model: {values[0]}", source)
                    source = re.sub(r"(?m)^effort: .*$", f"effort: {values[1]}", source)
                else:
                    source = re.sub(r"(?m)^model: .*$", f"model: {values[0]}", source)
                self.assertEqual(entry["file_type"], "managed-file")
                self.assertEqual(entry["mode"], "0600")
                self.assertEqual(entry["sha256"], sha256(source.encode()))

    def test_runtime_surfaces_are_schema_owned_and_complete(self) -> None:
        runtime = self.fixture["runtime_surfaces"]
        by_pattern = {entry["path_pattern"]: entry for entry in runtime}
        self.assertEqual(set(by_pattern), set(EXPECTED_RUNTIME_SURFACES))
        self.assertEqual(len(runtime), len(by_pattern))
        for pattern, (surface_class, owner, file_type, schema) in EXPECTED_RUNTIME_SURFACES.items():
            entry = by_pattern[pattern]
            self.assertNotIn("sha256", entry, entry["path_pattern"])
            self.assertEqual(entry["hash_policy"], "migration-preflight")
            self.assertEqual(entry["surface_class"], surface_class)
            self.assertEqual(entry["owner"], owner)
            self.assertEqual(entry["file_type"], file_type)
            self.assertEqual(entry["schema"], schema)

    def test_snapshot_schema_is_explicit(self) -> None:
        algorithms = self.fixture["snapshot_algorithms"]
        tree = algorithms["tree-sha256-v1"]
        self.assertEqual(tree["sort"], "relative-posix-path-utf8-bytes")
        self.assertEqual(tree["record"], "path\\0type\\0mode\\0value\\n")
        self.assertEqual(tree["file_value"], "sha256(raw-bytes)")
        self.assertEqual(tree["symlink_value"], "sha256(utf8-link-target)")
        index = algorithms["git-index-v1"]
        self.assertIn("intent_to_add", index["required_fields"])
        self.assertIn("ls_files_stage_sha256", index["required_fields"])

    def test_skill_fixture_is_only_a_derived_subset(self) -> None:
        subset = json.loads((FIXTURES / "v3.4.2-skill-inventory.json").read_text(encoding="utf-8"))
        expected = sorted(
            entry["path"] for entry in self.fixture["deterministic_surfaces"]
            if entry["surface_class"] in {"skill", "skill-reference", "skill-runtime"}
            and entry["path"].startswith("skills/")
        )
        self.assertEqual(subset["derived_from"], "v3.4.2-owned-surfaces.json")
        self.assertEqual(subset["deletion_authority"], False)
        self.assertEqual(subset["files"], expected)


if __name__ == "__main__":
    unittest.main()
