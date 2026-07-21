"""Focused contracts for the v4 eight-role templates and profile adapters."""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import tempfile
import textwrap
import tomllib
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from teamwork_tooling.evaluation import host_cli, host_matrix  # noqa: E402

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
        "researcher": ("gpt-5.6-terra-medium",),
        "explorer": ("gemini-3.5-flash",),
        "debugger": ("claude-opus-4-8-thinking-high",),
        "designer": ("gpt-5.6-sol-medium",),
        "planner": ("gpt-5.6-terra-medium",),
        "worker": ("composer-2.5-fast",),
        "plan-reviewer": ("claude-opus-4-8-thinking-high",),
        "reviewer": ("claude-fable-5-thinking-high",),
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
        "researcher": ("gemini-3.5-flash",),
        "explorer": ("gemini-3.5-flash",),
        "debugger": ("gpt-5.6-terra-medium",),
        "designer": ("gpt-5.6-terra-medium",),
        "planner": ("gpt-5.6-luna-medium",),
        "plan-reviewer": ("gpt-5.6-terra-medium",),
        "reviewer": ("claude-opus-4-8-thinking-high",),
    },
}


def minimal_trajectory_schema() -> dict[str, object]:
    return {
        "$id": "https://teamwork.example/schemas/host-trajectory-v4.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": sorted(host_matrix.TRAJECTORY_FIELDS),
        "properties": {
            **{field: {} for field in host_matrix.TRAJECTORY_FIELDS},
            "schema_version": {"const": host_matrix.SCHEMA_VERSION},
            "record_type": {"const": "teamwork_host_trajectory_v4"},
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
            "designer": (
                "only the evidence tracks that Root conditionally supplies",
                "challenge one frozen adversarial hypothesis",
                "audit one frozen adversarial search closure",
                "distinct host task identity",
                "unless the audit assignment explicitly includes the final ledger",
            ),
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

    def test_codex_root_arms_are_exactly_four_gpt55_profile_pairs(self) -> None:
        expected = {
            "performance-first-root-gpt55-low": ("performance-first", "gpt-5.5", "low"),
            "performance-first-root-gpt55-high": ("performance-first", "gpt-5.5", "high"),
            "cost-first-root-gpt55-low": ("cost-first", "gpt-5.5", "low"),
            "cost-first-root-gpt55-high": ("cost-first", "gpt-5.5", "high"),
        }
        self.assertEqual(expected, host_matrix.CODEX_ROOT_ARMS)
        for arm, (profile, model, effort) in expected.items():
            host_matrix._validate_codex_root_arm(arm, profile, model, effort)

        for blocked in (
            ("performance-first-root-terra-medium", "performance-first", "gpt-5.6-terra", "medium"),
            ("performance-first-root-sol-high", "performance-first", "gpt-5.6-sol", "high"),
            ("performance-first-root-gpt55-low", "cost-first", "gpt-5.5", "low"),
        ):
            with self.subTest(blocked=blocked):
                with self.assertRaisesRegex(host_matrix.HostMatrixError, "unsupported Codex Root arm"):
                    host_matrix._validate_codex_root_arm(*blocked)

        parser = host_cli.parser_for("codex")
        subcommands = next(
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        )
        arm_action = next(
            action for action in subcommands.choices["run"]._actions if action.dest == "arm"
        )
        self.assertEqual(tuple(expected), arm_action.choices)

    def test_candidate_fingerprint_keeps_legacy_helper_deterministic_but_binds_c5_evidence(self) -> None:
        legacy = {
            "scope_revision": "7" * 64,
            "candidate_id": "legacy-fixture",
            "candidate_tree_oid": "1" * 40,
            "repair_generation": 0,
            "base_commit": "2" * 40,
            "paths_manifest_sha256": "3" * 64,
            "entries": [],
        }
        self.assertEqual(
            host_matrix.sha256_bytes(host_matrix._canonical_json_bytes(legacy)),
            host_matrix._candidate_fingerprint(legacy),
        )

        partial = {**legacy, "official_doc_urls": list(host_matrix.OFFICIAL_DOC_URLS)}
        with self.assertRaises(host_matrix.HostMatrixError):
            host_matrix._candidate_fingerprint(partial)

        bound = {
            **legacy,
            "official_doc_urls": list(host_matrix.OFFICIAL_DOC_URLS),
            "official_doc_urls_sha256": host_matrix.sha256_bytes(
                host_matrix._canonical_json_bytes(list(host_matrix.OFFICIAL_DOC_URLS))
            ),
            "runtime_probe_source": host_matrix.RUNTIME_PROBE_SOURCE,
            "runtime_probe_source_sha256": host_matrix.sha256_bytes(
                host_matrix._canonical_json_bytes(host_matrix.RUNTIME_PROBE_SOURCE)
            ),
        }
        self.assertNotEqual(
            host_matrix._candidate_fingerprint(legacy),
            host_matrix._candidate_fingerprint(bound),
        )

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

    def test_host_dispatch_records_enforce_c5_host_nullability(self) -> None:
        schema = minimal_trajectory_schema()
        codex_dispatch = host_matrix._dispatch_record(
            host="codex",
            role="worker",
            invocation_id="parent-1",
            expectation={"model": "gpt-5.5", "effort": "high"},
        )
        cursor_dispatch = host_matrix._dispatch_record(
            host="cursor",
            role="plan-reviewer",
            invocation_id="parent-2",
            expectation={"model": "claude-opus-4-8-thinking-high", "effort": "cursor-managed"},
        )
        base = {
            "schema_version": 4,
            "record_type": "teamwork_host_trajectory_v4",
            "host_version": "test",
            "started_at": "s",
            "finished_at": "f",
            "case_id": "case",
            "profile": "performance-first",
            "selected_skill": "native",
            "tool_observations": ["command_execution"],
            "authority_observation": "workspace-write",
            "sanitized_input_sha256": "0" * 64,
            "artifact": {"path": "artifacts/x/trace.jsonl", "sha256": "1" * 64},
            "result": {"path": "artifacts/x/result.txt", "sha256": "2" * 64, "direct_success": True},
            "exit_status": 0,
            "status": "PASS",
            "privacy_scan": "PASS",
            "failure_classification": None,
        }
        codex = {
            **base,
            "host": "codex",
            "invocation_id": "parent-1",
            "arm": "performance-first-root-gpt55-low",
            "parent_model": "gpt-5.5",
            "parent_effort": "low",
            "role_identity": "worker",
            "actual_model": "gpt-5.5",
            "actual_effort": "high",
            "dispatches": [codex_dispatch],
        }
        host_matrix.validate_trajectory(codex, schema)
        codex["dispatches"] = [{**codex_dispatch, "model_override_present": True}]
        with self.assertRaisesRegex(host_matrix.HostMatrixError, "must not request child model/effort overrides"):
            host_matrix.validate_trajectory(codex, schema)

        cursor = {
            **base,
            "host": "cursor",
            "invocation_id": "parent-2",
            "arm": "performance-first",
            "parent_model": "cursor-managed",
            "parent_effort": "cursor-managed",
            "role_identity": "plan-reviewer",
            "actual_model": "claude-opus-4-8-thinking-high",
            "actual_effort": "cursor-managed",
            "dispatches": [cursor_dispatch],
        }
        host_matrix.validate_trajectory(cursor, schema)
        cursor["dispatches"] = [{**cursor_dispatch, "fork_turns": "none"}]
        with self.assertRaisesRegex(host_matrix.HostMatrixError, "Cursor dispatch must leave Codex-only fields null"):
            host_matrix.validate_trajectory(cursor, schema)

    def test_codex_0144_skill_file_reads_do_not_forge_role_dispatch(self) -> None:
        events = [
            {"type": "thread.started"},
            {
                "type": "item.started",
                "item": {
                    "type": "command_execution",
                    "command": "/bin/zsh -lc \"sed -n '1,240p' scenario/design-probe.txt\"",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "/bin/zsh -lc \"sed -n '1,240p' /tmp/home/.agents/skills/teamwork-design/SKILL.md\"",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "/bin/zsh -lc \"sed -n '1,220p' skills/teamwork-plan/SKILL.md\"",
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "/bin/zsh -lc \"sed -n '1,220p' skills/teamwork-review/SKILL.md\"",
                },
            },
        ]
        observations = host_matrix._trajectory_observations(
            host="codex",
            events=events,
            case={"selected_skill": "teamwork-design", "authority": "read-only"},
            parent_model="gpt-5.5",
            parent_effort="low",
        )

        self.assertEqual(["teamwork-design", "teamwork-plan", "teamwork-review"], host_matrix.observed_skills(events))
        self.assertEqual("teamwork-design", observations["selected_skill"])
        self.assertEqual("gpt-5.5", observations["actual_model"])
        self.assertEqual("low", observations["actual_effort"])
        self.assertEqual("read-only", observations["authority"])
        self.assertEqual([], observations["roles"])

    def test_cursor_adapter_uses_existing_gui_agent_command_and_rejects_wrappers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            cursor = root / "cursor"
            cursor.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import sys
                    args = sys.argv[1:]
                    if args == ["agent", "--help"]:
                        print("cursor agent help")
                        raise SystemExit(0)
                    if args == ["--version"]:
                        print("cursor test")
                        raise SystemExit(0)
                    raise SystemExit(1)
                    """
                ),
                encoding="utf-8",
            )
            cursor.chmod(0o755)
            cursor_agent = root / "cursor-agent"
            cursor_agent.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            cursor_agent.chmod(0o755)
            wrapper = root / "cursor-wrapper"
            wrapper.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            wrapper.chmod(0o755)

            self.assertEqual([str(cursor), "agent"], host_matrix._cursor_command_prefix(str(cursor)))
            self.assertEqual([str(cursor_agent)], host_matrix._cursor_command_prefix(str(cursor_agent)))
            with self.assertRaisesRegex(host_matrix.HostMatrixError, "temporary wrappers are rejected"):
                host_matrix._cursor_command_prefix(str(wrapper))

    def test_codex_argv_skips_git_check_only_for_sealed_archive_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            tree = root / "tree"
            tree.mkdir()
            scenario_parent = root / "scenarios"
            scenario_parent.mkdir()
            sealed = host_matrix._apply_scenario(
                tree,
                scenario_parent / "candidate",
                {"files": [{"path": "case.txt", "content": "ready\n"}]},
            )
            argv = host_matrix._host_argv(
                "codex", ["codex"], sealed, "do work", "workspace-write", "gpt-5.5", "low"
            )
            self.assertEqual(["codex", "exec"], argv[:2])
            self.assertIn("--skip-git-repo-check", argv)
            self.assertLess(argv.index("--skip-git-repo-check"), argv.index("--cd"))
            self.assertEqual(str(sealed.path), argv[argv.index("--cd") + 1])
            self.assertEqual("do work", argv[-1])
            self.assertEqual("gpt-5.5", argv[argv.index("--model") + 1])
            self.assertEqual('model_reasoning_effort="low"', argv[argv.index("-c") + 1])

            raw = host_matrix._host_argv(
                "codex", ["codex"], sealed.path, "do work", "workspace-write", "gpt-5.5", "low"
            )
            self.assertNotIn("--skip-git-repo-check", raw)

            git_tree = root / "git-tree"
            git_tree.mkdir()
            (git_tree / ".git").mkdir()
            with self.assertRaisesRegex(host_matrix.HostMatrixError, "must not contain a Git repository"):
                host_matrix._apply_scenario(git_tree, scenario_parent / "git-candidate", {"files": []})

    def test_codex_auth_materializes_only_auth_file_without_leaking_secret(self) -> None:
        secret = "dummy-secret-token-for-host-matrix-test"
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source_home = root / "source-codex"
            source_home.mkdir(mode=0o700)
            auth = source_home / "auth.json"
            auth.write_text(secret, encoding="utf-8")
            auth.chmod(0o600)
            (source_home / "history.jsonl").write_text(secret, encoding="utf-8")
            (source_home / "session_index.jsonl").write_text(secret, encoding="utf-8")

            run_home = root / "run-home"
            run_home.mkdir(mode=0o700)
            env = host_matrix._codex_run_environment(run_home, auth)
            copied = pathlib.Path(env["CODEX_HOME"]) / "auth.json"
            self.assertTrue(copied.is_file())
            self.assertEqual(secret, copied.read_text(encoding="utf-8"))
            self.assertEqual(0o600, copied.stat().st_mode & 0o777)
            self.assertEqual({"auth.json"}, {path.name for path in pathlib.Path(env["CODEX_HOME"]).iterdir()})
            self.assertNotIn(secret, "\n".join(env.values()))

            output_root = root / "outputs"
            output_root.mkdir(mode=0o700)
            output = output_root / "trajectory.jsonl"
            case = {"evidence": {"kind": "trace", "markers": ["public-marker"]}, "private_markers": [secret]}
            ok, artifact, result, failure = host_matrix._direct_scenario_evidence(
                case=case,
                scenario=root,
                events=[
                    {"type": "tool_call", "tool_name": "shell"},
                    {"type": "tool_result", "value": f"public-marker {secret}"},
                ],
                output=output,
                invocation_id="invocation",
                workspace_before=None,
                forbidden_output_markers=[secret.encode()],
            )
            self.assertFalse(ok)
            self.assertEqual("auth-output-leak", failure)
            self.assertEqual({}, artifact)
            self.assertEqual({}, result)
            self.assertEqual([], list(output_root.rglob("*")))

    def test_codex_auth_source_rejects_symlink_permissive_and_missing_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source_home = root / "source-codex"
            source_home.mkdir(mode=0o700)
            target = root / "target-auth.json"
            target.write_text("dummy-secret", encoding="utf-8")
            target.chmod(0o600)
            symlink = source_home / "auth.json"
            symlink.symlink_to(target)
            with self.assertRaisesRegex(host_matrix.HostMatrixError, "must not be a symlink"):
                host_matrix._validate_codex_auth_source(symlink)

            symlink.unlink()
            symlink.write_text("dummy-secret", encoding="utf-8")
            symlink.chmod(0o644)
            with self.assertRaisesRegex(host_matrix.HostMatrixError, "permissions must be private"):
                host_matrix._validate_codex_auth_source(symlink)

            with self.assertRaisesRegex(host_matrix.HostMatrixError, "^codex-auth-unavailable$"):
                host_matrix._preflight_codex_auth_source({"CODEX_HOME": str(root / "missing-codex")})

    def test_c5_manifest_path_is_exact_external_exception(self) -> None:
        original_root = host_matrix.C5_TEMP_ROOT
        original_manifest = host_matrix.C5_TEMP_MANIFEST
        with tempfile.TemporaryDirectory() as temporary:
            tmp_real = pathlib.Path(temporary) / "real-tmp"
            tmp_real.mkdir()
            temp_root = tmp_real / "teamwork-4.1.0-c5"
            temp_root.mkdir(mode=0o700)
            lexical_root = pathlib.Path("/tmp/teamwork-4.1.0-c5")
            manifest = temp_root / "manifest.json"
            manifest.write_text("{}\n", encoding="utf-8")
            paths = temp_root / "v4-release-paths.json"
            paths.write_text("{}\n", encoding="utf-8")

            host_matrix.C5_TEMP_ROOT = lexical_root
            host_matrix.C5_TEMP_MANIFEST = lexical_root / "manifest.json"
            original_realpath = host_matrix.os.path.realpath
            host_matrix.os.path.realpath = lambda value: str(tmp_real) if value == "/tmp" else original_realpath(value)
            try:
                allowed_manifest, allowed_root = host_matrix._candidate_manifest_path(ROOT, pathlib.Path("/tmp/teamwork-4.1.0-c5/manifest.json"))
                self.assertEqual(host_matrix._absolute_path(temp_root / "manifest.json"), allowed_manifest)
                self.assertEqual(host_matrix._absolute_path(temp_root), allowed_root)
                for blocked in (
                    pathlib.Path("/tmp/teamwork-4.1.0-c5/neighbor.json"),
                    pathlib.Path("/tmp/manifest.json"),
                    pathlib.Path("/tmp/teamwork-4.1.0-c5/nested/manifest.json"),
                ):
                    with self.subTest(blocked=blocked):
                        with self.assertRaises(host_matrix.HostMatrixError):
                            host_matrix._candidate_manifest_path(ROOT, blocked)
            finally:
                host_matrix.os.path.realpath = original_realpath
                host_matrix.C5_TEMP_ROOT = original_root
                host_matrix.C5_TEMP_MANIFEST = original_manifest

    def test_c5_manifest_temp_root_requires_private_owner_mode(self) -> None:
        original_root = host_matrix.C5_TEMP_ROOT
        original_manifest = host_matrix.C5_TEMP_MANIFEST
        with tempfile.TemporaryDirectory() as temporary:
            tmp_real = pathlib.Path(temporary) / "real-tmp"
            tmp_real.mkdir()
            temp_root = tmp_real / "teamwork-4.1.0-c5"
            temp_root.mkdir(mode=0o755)
            manifest = temp_root / "manifest.json"
            manifest.write_text("{}\n", encoding="utf-8")
            lexical_root = pathlib.Path("/tmp/teamwork-4.1.0-c5")
            host_matrix.C5_TEMP_ROOT = lexical_root
            host_matrix.C5_TEMP_MANIFEST = lexical_root / "manifest.json"
            original_realpath = host_matrix.os.path.realpath
            host_matrix.os.path.realpath = lambda value: str(tmp_real) if value == "/tmp" else original_realpath(value)
            try:
                with self.assertRaisesRegex(host_matrix.HostMatrixError, "mode 0700"):
                    host_matrix._candidate_manifest_path(ROOT, pathlib.Path("/tmp/teamwork-4.1.0-c5/manifest.json"))
            finally:
                host_matrix.os.path.realpath = original_realpath
                host_matrix.C5_TEMP_ROOT = original_root
                host_matrix.C5_TEMP_MANIFEST = original_manifest

    def test_c5_manifest_rejects_candidate_dir_and_manifest_symlinks(self) -> None:
        original_root = host_matrix.C5_TEMP_ROOT
        original_manifest = host_matrix.C5_TEMP_MANIFEST
        with tempfile.TemporaryDirectory() as temporary:
            tmp_real = pathlib.Path(temporary) / "real-tmp"
            tmp_real.mkdir()
            real_candidate = pathlib.Path(temporary) / "real-candidate"
            real_candidate.mkdir(mode=0o700)
            (real_candidate / "manifest.json").write_text("{}\n", encoding="utf-8")
            symlink_candidate = tmp_real / "teamwork-4.1.0-c5"
            symlink_candidate.symlink_to(real_candidate, target_is_directory=True)
            lexical_root = pathlib.Path("/tmp/teamwork-4.1.0-c5")
            host_matrix.C5_TEMP_ROOT = lexical_root
            host_matrix.C5_TEMP_MANIFEST = lexical_root / "manifest.json"
            original_realpath = host_matrix.os.path.realpath
            host_matrix.os.path.realpath = lambda value: str(tmp_real) if value == "/tmp" else original_realpath(value)
            try:
                with self.assertRaisesRegex(host_matrix.HostMatrixError, "non-symlink directory"):
                    host_matrix._candidate_manifest_path(ROOT, pathlib.Path("/tmp/teamwork-4.1.0-c5/manifest.json"))
                symlink_candidate.unlink()
                real_dir = tmp_real / "teamwork-4.1.0-c5"
                real_dir.mkdir(mode=0o700)
                target = pathlib.Path(temporary) / "outside-manifest.json"
                target.write_text("{}\n", encoding="utf-8")
                (real_dir / "manifest.json").symlink_to(target)
                with self.assertRaisesRegex(host_matrix.HostMatrixError, "must not be a symlink"):
                    host_matrix._candidate_manifest_path(ROOT, pathlib.Path("/tmp/teamwork-4.1.0-c5/manifest.json"))
            finally:
                host_matrix.os.path.realpath = original_realpath
                host_matrix.C5_TEMP_ROOT = original_root
                host_matrix.C5_TEMP_MANIFEST = original_manifest

    def test_c5_installed_output_allows_planned_macos_tmp_alias_path(self) -> None:
        original_root = host_matrix.C5_TEMP_ROOT
        original_manifest = host_matrix.C5_TEMP_MANIFEST
        with tempfile.TemporaryDirectory() as temporary:
            tmp_real = pathlib.Path(temporary) / "real-tmp"
            tmp_real.mkdir()
            temp_root = tmp_real / "teamwork-4.1.0-c5"
            temp_root.mkdir(mode=0o700)
            lexical_root = pathlib.Path("/tmp/teamwork-4.1.0-c5")
            host_matrix.C5_TEMP_ROOT = lexical_root
            host_matrix.C5_TEMP_MANIFEST = lexical_root / "manifest.json"
            original_realpath = host_matrix.os.path.realpath
            host_matrix.os.path.realpath = lambda value: str(tmp_real) if value == "/tmp" else original_realpath(value)
            try:
                output = host_matrix._prepare_absolute_output_path(
                    pathlib.Path("/tmp/teamwork-4.1.0-c5/outputs/installed-v4/slice/trajectory.jsonl")
                )
                expected = host_matrix._absolute_path(temp_root / "outputs/installed-v4/slice/trajectory.jsonl")
                self.assertEqual(expected, output)
                self.assertTrue(output.parent.is_dir())
                self.assertFalse(output.exists())
            finally:
                host_matrix.os.path.realpath = original_realpath
                host_matrix.C5_TEMP_ROOT = original_root
                host_matrix.C5_TEMP_MANIFEST = original_manifest

    def test_c5_installed_output_rejects_neighbor_and_subdir_symlink(self) -> None:
        original_root = host_matrix.C5_TEMP_ROOT
        original_manifest = host_matrix.C5_TEMP_MANIFEST
        with tempfile.TemporaryDirectory() as temporary:
            tmp_real = pathlib.Path(temporary) / "real-tmp"
            tmp_real.mkdir()
            temp_root = tmp_real / "teamwork-4.1.0-c5"
            temp_root.mkdir(mode=0o700)
            lexical_root = pathlib.Path("/tmp/teamwork-4.1.0-c5")
            host_matrix.C5_TEMP_ROOT = lexical_root
            host_matrix.C5_TEMP_MANIFEST = lexical_root / "manifest.json"
            original_realpath = host_matrix.os.path.realpath
            host_matrix.os.path.realpath = lambda value: str(tmp_real) if value == "/tmp" else original_realpath(value)
            try:
                for blocked in (
                    pathlib.Path("/tmp/teamwork-4.1.0-c5-neighbor/outputs/installed-v4/trajectory.jsonl"),
                    pathlib.Path("/private/tmp/teamwork-4.1.0-c5/outputs/installed-v4/trajectory.jsonl"),
                    pathlib.Path("/tmp/teamwork-4.1.0-c5/../outside/outputs/installed-v4/trajectory.jsonl"),
                    pathlib.Path("/tmp/teamwork-4.1.0-c5/installed-v4/slice/trajectory.jsonl"),
                ):
                    with self.subTest(blocked=blocked):
                        with self.assertRaises(host_matrix.HostMatrixError):
                            host_matrix._prepare_absolute_output_path(blocked)
                outside = pathlib.Path(temporary) / "outside"
                outside.mkdir()
                (temp_root / "outputs").symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(host_matrix.HostMatrixError, "must not contain a symlink"):
                    host_matrix._prepare_absolute_output_path(
                        pathlib.Path("/tmp/teamwork-4.1.0-c5/outputs/installed-v4/slice/trajectory.jsonl")
                    )
            finally:
                host_matrix.os.path.realpath = original_realpath
                host_matrix.C5_TEMP_ROOT = original_root
                host_matrix.C5_TEMP_MANIFEST = original_manifest


if __name__ == "__main__":
    unittest.main()
