#!/usr/bin/env python3
"""Enforce W0's live candidate, ownership, deletion, and CAS contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
BASE = "93572a3e8029b5348ee31d2a65b0c9a06b45beed"
PLAN = "docs/teamwork/plans/2026-07-19-skill-architecture-v4-redesign-v2.md"
W0_PATHS = {
    "scripts/tests/fixtures/v3.4.2-owned-surfaces.json",
    "scripts/tests/fixtures/v3.4.2-skill-inventory.json",
    "scripts/tests/fixtures/v4-path-ownership.json",
    "evals/teamwork/ledgers/v4-capability-migration.jsonl",
    "scripts/tests/test_v342_owned_surfaces.py",
    "scripts/tests/test_v4_path_ownership.py",
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


def normalized_delta() -> dict[str, dict[str, str]]:
    """Use NUL-delimited Git output so status/path normalization is stable."""
    raw = git("diff", "--name-status", "-z", "--find-renames", BASE, binary=True)
    parts = raw.decode("utf-8").split("\0")
    result: dict[str, dict[str, str]] = {}
    index = 0
    while index < len(parts) - 1:
        token = parts[index]
        index += 1
        if not token:
            break
        status = token[0]
        if status in {"R", "C"}:
            old_path, path = parts[index], parts[index + 1]
            index += 2
            result[path] = {"observed_status": status, "old_path": old_path}
        else:
            path = parts[index]
            index += 1
            result[path] = {"observed_status": status}
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", binary=True)
    for raw_path in untracked.decode("utf-8").split("\0"):
        if raw_path:
            result.setdefault(raw_path.rstrip("/"), {"observed_status": "A"})
    staged_renames = {
        "scripts/plugin-runtime-root.py": "skills/using-teamwork/scripts/plugin-runtime-root.py",
        "plugins/teamwork-skill/scripts/plugin-runtime-root.py":
            "plugins/teamwork-skill/skills/using-teamwork/scripts/plugin-runtime-root.py",
    }
    for destination, source in staged_renames.items():
        if result.get(destination) == {"observed_status": "R", "old_path": source}:
            continue
        if result.get(destination) != {"observed_status": "A"} \
                or result.get(source) != {"observed_status": "D"}:
            raise AssertionError(f"expected candidate-index rename inputs for {source} -> {destination}")
        result.pop(source)
        result[destination] = {"observed_status": "R", "old_path": source}
    return result


def matches(rule: dict, path: str) -> bool:
    if path in rule.get("exclude", []) or any(path.startswith(value) for value in rule.get("exclude_prefixes", [])):
        return False
    return path in rule.get("paths", []) or any(path.startswith(value) for value in rule.get("prefixes", []))


def resolve(mapping: dict, path: str) -> list[str]:
    if any(path.startswith(value) for value in mapping["forbidden_prefixes"]):
        return ["FORBIDDEN"]
    owners = [rule["owner"] for rule in mapping["owners"] if matches(rule, path)]
    return owners or [mapping["default_owner"]]


def mode_of(path: pathlib.Path) -> str:
    return f"{stat.S_IMODE(path.lstat().st_mode):04o}"


def tree_sha256(root: pathlib.Path) -> str:
    lines: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda value: value.relative_to(root).as_posix().encode("utf-8")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            kind = "symlink"
            value = hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
        elif path.is_file():
            kind = "file"
            value = hashlib.sha256(path.read_bytes()).hexdigest()
        elif path.is_dir():
            kind, value = "directory", "-"
        else:
            kind, value = "other", "-"
        lines.append(f"{relative}\0{kind}\0{mode_of(path)}\0{value}\n")
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def current_preimage(path: str) -> dict[str, str | None]:
    target = REPO_ROOT / path
    if target.is_symlink():
        return {"file_type": "symlink", "mode": mode_of(target), "sha256": hashlib.sha256(os.readlink(target).encode()).hexdigest()}
    if target.is_file():
        return {"file_type": "file", "mode": mode_of(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    if target.is_dir():
        return {"file_type": "directory", "mode": mode_of(target), "sha256": tree_sha256(target)}
    return {"file_type": "absent", "mode": None, "sha256": None}


def base_preimage(path: str) -> dict[str, str | None]:
    fields = git("ls-tree", BASE, "--", path).strip().split()
    if not fields:
        return {"file_type": "absent", "mode": None, "sha256": None}
    mode, object_type, oid = fields[:3]
    if object_type != "blob":
        raise AssertionError(f"unsupported published preimage type for {path}: {object_type}")
    blob = git("cat-file", "blob", oid, binary=True)
    return {
        "file_type": "symlink" if mode == "120000" else "file",
        "mode": "0777" if mode == "120000" else ("0755" if mode == "100755" else "0644"),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def parse_debug_flags(value: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: str | None = None
    for line in value.splitlines():
        if line and not line[0].isspace():
            current = line
        elif current is not None and line.strip().startswith("size:") and "flags:" in line:
            flags = line.rsplit("flags:", 1)[1].strip()
            if int(flags, 16) & 0x20000000:
                records.append({"path": current, "flags": flags})
    return records


def index_snapshot() -> dict:
    raw_path = git("rev-parse", "--git-path", "index").strip()
    path = pathlib.Path(raw_path)
    path = path if path.is_absolute() else REPO_ROOT / path
    data = path.read_bytes()
    debug = git("ls-files", "--debug")
    stage = git("ls-files", "--stage")
    return {
        "index_path": raw_path,
        "file_type": "file",
        "mode": mode_of(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "write_tree": git("write-tree").strip(),
        "cached_raw": git("diff", "--cached", "--raw", "--full-index"),
        "unmerged": git("ls-files", "--unmerged"),
        "ls_files_debug_sha256": hashlib.sha256(debug.encode()).hexdigest(),
        "ls_files_stage_sha256": hashlib.sha256(stage.encode()).hexdigest(),
        "intent_to_add": parse_debug_flags(debug),
    }


FULL_OWNER_TABLE = {
    "W0-inventory": {"paths": W0_PATHS, "prefixes": set(), "exclude": set(), "exclude_prefixes": set()},
    "W1-evaluation": {
        "paths": {
            "scripts/teamwork_tooling/live_canary.py", "scripts/eval-teamwork.py",
            "scripts/run-teamwork-live-eval.py", "scripts/run-installed-teamwork-live-eval.py",
            "scripts/run-installed-cursor-teamwork-live-eval.py", "scripts/run-installed-claude-teamwork-live-eval.py",
            "scripts/run-teamwork-release-matrix.py", "scripts/test_eval_teamwork_mutations.py",
            "scripts/test_live_eval_runner.py", "scripts/tests/test_evaluation_contract_v4.py",
            "scripts/tests/test_eval_teamwork_compatibility.py", "scripts/tests/test_live_canary.py",
        },
        "prefixes": {"evals/teamwork/", "scripts/teamwork_tooling/evaluation/"},
        "exclude": {"evals/teamwork/ledgers/v4-capability-migration.jsonl"},
        "exclude_prefixes": {"evals/teamwork/outputs/installed-v4/"},
    },
    "W2-policy": {"paths": {"scripts/install/policy.sh", "scripts/tests/test_policy_contract_v4.py"}, "prefixes": set(), "exclude": set(), "exclude_prefixes": set()},
    "W2-skills": {"paths": {"scripts/tests/test_skill_topology_v4.py"}, "prefixes": {"skills/"}, "exclude": set(), "exclude_prefixes": set()},
    "W3-roles": {"paths": {"scripts/check-codex-routing.py", "scripts/install/profiles.sh", "scripts/tests/test_role_profiles_v4.py"}, "prefixes": {"templates/codex-agents/", "templates/cursor-agents/", "templates/claude-agents/"}, "exclude": set(), "exclude_prefixes": set()},
    "W3-installer": {"paths": {"install.sh", "scripts/install/common.sh", "scripts/install/targets.sh", "scripts/check-update.sh", "scripts/tests/test_install_cli_compatibility.py", "scripts/tests/test_v342_skill_upgrade.py"}, "prefixes": set(), "exclude": set(), "exclude_prefixes": set()},
    "W4-artifacts": {"paths": {"scripts/discussion-transaction.py", "scripts/discussion-write-evidence.py", "scripts/teamwork_tooling/discussion_lifecycle.py", "scripts/plugin-runtime-root.py", "scripts/grill_contract.py", "scripts/tests/test_discussion_transaction.py", "scripts/tests/test_discussion_index_safety.py", "scripts/tests/test_design_artifact_schema.py", "scripts/tests/test_goal_state_lifecycle.py", "scripts/tests/test_active_artifact_currentness.py", "scripts/tests/test_discussion_artifact_schema.py", "scripts/tests/test_discussion_lifecycle.py"}, "prefixes": {"templates/teamwork-memory/"}, "exclude": set(), "exclude_prefixes": set()},
    "W5-init": {"paths": {"scripts/init-project-files.py", "scripts/init-project.sh", "scripts/validate_teamwork_index.py", "scripts/tests/test_init_project_files.py", "scripts/tests/test_init_project_aba.py", "scripts/tests/test_teamwork_index_init.py"}, "prefixes": set(), "exclude": set(), "exclude_prefixes": set()},
    "W6-bundle-validation": {"paths": {"scripts/build-codex-plugin.py", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json", "VERSION", "scripts/validate.sh", "scripts/teamwork_tooling/privacy_scan.py", "scripts/teamwork_tooling/instruction_footprint.py", "scripts/tests/test_privacy_scan.py", "scripts/tests/test_instruction_footprint.py", "scripts/test_codex_routing_config.py", "scripts/test_codex_app_server_user_input.py"}, "prefixes": {"plugins/teamwork-skill/", "scripts/validation/"}, "exclude": set(), "exclude_prefixes": set()},
    "W8-docs": {"paths": {".gitignore", "README.md", "README.en.md", "CODEX.md", "CURSOR.md", "CLAUDE.md", "docs/architecture.md", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md", "CHANGELOG.en.md"}, "prefixes": set(), "exclude": set(), "exclude_prefixes": set()},
    "W9-release-index": {"paths": {"scripts/release-index-transaction.py", "scripts/tests/test_release_index_transaction.py"}, "prefixes": set(), "exclude": set(), "exclude_prefixes": set()},
    "ROOT-RUNTIME": {"paths": set(), "prefixes": {"docs/teamwork/research/", "docs/teamwork/design/", "docs/teamwork/discussion/", "docs/teamwork/plans/", "docs/teamwork/reports/", "docs/teamwork/workflows/", "evals/teamwork/outputs/installed-v4/"}, "exclude": set(), "exclude_prefixes": set()},
}
EXPECTED_RUNTIME_OUTPUTS = [
    "docs/teamwork/reports/v4-release-paths.json",
    "docs/teamwork/reports/v4-release-candidate.json",
    "docs/teamwork/reports/v4-release-index-state/candidate.index",
    "docs/teamwork/reports/v4-implementation-review.json",
    "docs/teamwork/reports/v4-release-commit-message.txt",
    "docs/teamwork/reports/v4-release-notes.md",
    "evals/teamwork/outputs/installed-v4/reviewer-acceptance.jsonl",
    "evals/teamwork/outputs/installed-v4/codex/performance-first.jsonl",
    "evals/teamwork/outputs/installed-v4/codex/cost-first.jsonl",
    "evals/teamwork/outputs/installed-v4/cursor/performance-first.jsonl",
    "evals/teamwork/outputs/installed-v4/cursor/cost-first.jsonl",
    "evals/teamwork/outputs/installed-v4/claude/performance-first.jsonl",
    "evals/teamwork/outputs/installed-v4/claude/cost-first.jsonl",
    "evals/teamwork/outputs/installed-v4/matrix-summary.json",
]


class V4PathOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = json.loads((FIXTURES / "v4-path-ownership.json").read_text())
        cls.inventory = json.loads((FIXTURES / "v3.4.2-owned-surfaces.json").read_text())
        cls.ledger = [json.loads(line) for line in (REPO_ROOT / "evals/teamwork/ledgers/v4-capability-migration.jsonl").read_text().splitlines() if line]

    def test_authoritative_owner_table_equals_the_accepted_plan_table(self) -> None:
        self.assertEqual(self.mapping["schema_version"], 1)
        self.assertEqual(self.mapping["base_commit"], BASE)
        self.assertEqual(self.mapping["default_owner"], "FORBIDDEN")
        self.assertEqual(self.mapping["forbidden_prefixes"], [".claude/"])
        actual = {
            rule["owner"]: {
                "paths": set(rule["paths"]), "prefixes": set(rule["prefixes"]),
                "exclude": set(rule.get("exclude", [])), "exclude_prefixes": set(rule.get("exclude_prefixes", [])),
            }
            for rule in self.mapping["owners"]
        }
        self.assertEqual(actual, FULL_OWNER_TABLE)
        self.assertEqual(self.mapping["declared_runtime_outputs"], EXPECTED_RUNTIME_OUTPUTS)

    def test_codex_role_routing_validator_is_owned_with_role_templates(self) -> None:
        self.assertEqual(
            resolve(self.mapping, "scripts/check-codex-routing.py"),
            ["W3-roles"],
        )

    def test_live_normalized_delta_equals_the_candidate_freeze(self) -> None:
        metadata = self.ledger[0]
        raw_live = normalized_delta()
        live = {
            path: observed for path, observed in raw_live.items()
            if resolve(self.mapping, path) != ["FORBIDDEN"]
        }
        self.assertEqual(sum(row.get("record_type") == "metadata" for row in self.ledger), 1)
        all_candidate_rows = [row for row in self.ledger[1:] if row["record_type"] == "candidate-path"]
        protected_rows = [row for row in all_candidate_rows if resolve(self.mapping, row["path"]) == ["FORBIDDEN"]]
        candidate_rows = [row for row in all_candidate_rows if row not in protected_rows]
        self.assertTrue(all(row["disposition"] == "preserve-user" and row["release_candidate_eligible"] is False for row in protected_rows))
        if os.environ.get("TEAMWORK_CANDIDATE_ISOLATED") == "1":
            self.assertFalse((REPO_ROOT / ".claude").exists())
        else:
            self.assertEqual({row["path"] for row in protected_rows}, {path for path in raw_live if resolve(self.mapping, path) == ["FORBIDDEN"]})
        self.assertEqual(len(candidate_rows), len(live))
        self.assertEqual(len({row["path"] for row in candidate_rows}), len(candidate_rows))
        candidates = {row["path"]: row for row in candidate_rows}
        self.assertEqual(
            [row["path"] for row in candidate_rows if row.get("self_referential_preimage")],
            [
                "evals/teamwork/ledgers/v4-capability-migration.jsonl",
                "plugins/teamwork-skill/evals/teamwork/ledgers/v4-capability-migration.jsonl",
            ],
        )
        self.assertEqual({path for path in metadata["frozen_candidate_paths"] if resolve(self.mapping, path) != ["FORBIDDEN"]}, set(live))
        self.assertEqual(set(candidates), set(live))
        self.assertTrue(
            {path for path in metadata["initial_frozen_candidate_paths"] if resolve(self.mapping, path) != ["FORBIDDEN"]}
            <= set(live)
        )
        for path, observed in live.items():
            self.assertEqual(candidates[path]["observed_status"], observed["observed_status"], path)
            self.assertEqual(candidates[path].get("old_path"), observed.get("old_path"), path)
            self.assertEqual(
                candidates[path]["base_preimage"],
                base_preimage(observed.get("old_path", path)),
                path,
            )
            self.assertEqual(
                candidates[path]["release_candidate_eligible"],
                candidates[path]["disposition"] != "preserve-user",
                path,
            )
            if candidates[path].get("self_referential_preimage"):
                self.assertEqual(
                    candidates[path]["preimage"],
                    {"file_type": "absent", "mode": None, "sha256": None},
                    path,
                )
            else:
                self.assertEqual(candidates[path]["preimage"], current_preimage(path), path)
        self.assertIn("scripts/release-index-transaction.py", candidates)
        self.assertIn("scripts/tests/test_release_index_transaction.py", candidates)

    def test_exact_one_owner_covers_delta_generated_runtime_and_ledger_paths(self) -> None:
        paths = set(normalized_delta())
        paths.update(entry["path"] for entry in self.inventory["deterministic_surfaces"] if entry["path"].startswith("plugins/teamwork-skill/"))
        paths.update(self.mapping["declared_runtime_outputs"])
        for row in self.ledger[1:]:
            path = row.get("path")
            if isinstance(path, str) and not path.startswith(("managed://", "runtime://", "git-index://")):
                paths.add(path.rstrip("/**"))
        for path in sorted(paths):
            owners = resolve(self.mapping, path)
            self.assertEqual(len(owners), 1, (path, owners))
            if path in normalized_delta() and owners == ["FORBIDDEN"]:
                self.assertTrue(path.startswith(".claude/"), f"unmapped candidate path: {path}")

    def test_overlap_and_missing_detection(self) -> None:
        mutated = copy.deepcopy(self.mapping)
        path = next(iter(W0_PATHS))
        mutated["owners"].append({"owner": "DUPLICATE", "paths": [path], "prefixes": [], "exclude": [], "exclude_prefixes": []})
        self.assertEqual(len([rule["owner"] for rule in mutated["owners"] if matches(rule, path)]), 2)
        self.assertEqual(resolve(self.mapping, "unplanned/new-file.txt"), ["FORBIDDEN"])

    def test_ledger_owner_inventory_capability_and_deletion_contract(self) -> None:
        metadata, records = self.ledger[0], self.ledger[1:]
        self.assertEqual(metadata["record_type"], "metadata")
        self.assertEqual(metadata["schema_version"], 1)
        self.assertEqual(metadata["base_commit"], BASE)
        self.assertIs(metadata["index_release_authority"], False)
        self.assertEqual(
            metadata["allowed_dispositions"],
            ["reuse", "revise", "restore", "retire", "preserve-user"],
        )
        self.assertEqual(
            metadata["frozen_candidate_paths"],
            sorted(set(metadata["frozen_candidate_paths"]), key=lambda value: value.encode("utf-8")),
        )
        self.assertEqual(
            metadata["initial_frozen_candidate_paths"],
            sorted(set(metadata["initial_frozen_candidate_paths"]), key=lambda value: value.encode("utf-8")),
        )
        self.assertTrue(set(metadata["initial_frozen_candidate_paths"]) <= set(metadata["frozen_candidate_paths"]))
        self.assertTrue(
            {row["record_type"] for row in records}
            <= {"candidate-path", "published-surface", "capability", "forbidden-snapshot", "git-index"}
        )
        expected_surfaces = {
            entry.get("path", entry.get("path_pattern"))
            for section in ("deterministic_surfaces", "runtime_surfaces")
            for entry in self.inventory[section]
        }
        surface_rows = [row for row in records if row["record_type"] == "published-surface"]
        self.assertEqual(len(surface_rows), len(expected_surfaces))
        self.assertEqual(len({row["source_id"] for row in surface_rows}), len(surface_rows))
        surfaces = {row["source_id"]: row for row in surface_rows}
        self.assertEqual(set(surfaces), expected_surfaces)
        for section in ("deterministic_surfaces", "runtime_surfaces"):
            for entry in self.inventory[section]:
                source_id = entry.get("path", entry.get("path_pattern"))
                row = surfaces[source_id]
                self.assertEqual(row["owner"], entry["owner"], source_id)
                if section == "deterministic_surfaces":
                    self.assertEqual(
                        row["preimage"],
                        {key: entry[key] for key in ("file_type", "mode", "sha256")},
                        source_id,
                    )
                else:
                    self.assertEqual(
                        row["preimage"],
                        {
                            "file_type": entry["file_type"], "mode": None, "sha256": None,
                            "schema": entry["schema"], "hash_policy": "migration-preflight",
                        },
                        source_id,
                    )
        capability_rows = [row for row in records if row["record_type"] == "capability"]
        capabilities = [row["source_id"] for row in capability_rows]
        expected_cases = set(git("ls-tree", "-r", "--name-only", BASE, "--", "evals/teamwork/cases").splitlines())
        rubric = json.loads(git("show", f"{BASE}:evals/teamwork/rubrics/behavioral-contracts.json"))
        expected_rubrics = {f"rubric:{row['name']}" for row in rubric["dimensions"]}
        expected_accepted = {
            f"accepted:{json.loads(line)['change_id']}"
            for line in git("show", f"{BASE}:evals/teamwork/ledgers/accepted.jsonl").splitlines()
            if line.strip()
        }
        self.assertEqual(set(capabilities), expected_cases | expected_rubrics | expected_accepted)
        self.assertEqual(len(capabilities), len(set(capabilities)))
        ledger_ids = [row["ledger_id"] for row in records]
        self.assertEqual(len(ledger_ids), len(set(ledger_ids)))
        accepted_hashes = {
            f"accepted:{json.loads(line)['change_id']}": hashlib.sha256(line.encode()).hexdigest()
            for line in git("show", f"{BASE}:evals/teamwork/ledgers/accepted.jsonl").splitlines()
            if line.strip()
        }
        rubric_hashes = {
            f"rubric:{dimension['name']}": hashlib.sha256(
                json.dumps(dimension, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            for dimension in rubric["dimensions"]
        }
        for row in capability_rows:
            source_id = row["source_id"]
            if source_id in expected_cases:
                expected_hash = hashlib.sha256(
                    git("show", f"{BASE}:{source_id}", binary=True)
                ).hexdigest()
            elif source_id in rubric_hashes:
                expected_hash = rubric_hashes[source_id]
            else:
                expected_hash = accepted_hashes[source_id]
            self.assertEqual(
                row["preimage"],
                {"file_type": "logical-capability", "mode": "0644", "sha256": expected_hash},
                source_id,
            )
        for row in records:
            self.assertIn(row["disposition"], {"reuse", "revise", "restore", "retire", "preserve-user"})
            self.assertTrue(row["owner"])
            self.assertTrue(row["evidence"])
            self.assertTrue(row["reason"])
            self.assertIn("preimage", row)
            if row.get("release_candidate_eligible"):
                owner = resolve(self.mapping, row["path"])
                self.assertNotEqual(owner, ["FORBIDDEN"], row["path"])
                self.assertEqual(owner, [row["owner"]], row["path"])
            if row.get("record_type") == "candidate-path" and row["observed_status"] == "D":
                self.assertIn(row["disposition"], {"restore", "retire"}, row["path"])
                if row["disposition"] == "restore":
                    destination = row.get("destination")
                    self.assertIsInstance(destination, dict, row["path"])
                    self.assertEqual(resolve(self.mapping, destination["path"]), [destination["owner"]], row["path"])
                else:
                    retirement = row.get("retirement")
                    self.assertIsInstance(retirement, dict, row["path"])
                    self.assertEqual(retirement.get("accepted_plan"), PLAN, row["path"])
                    self.assertTrue(retirement.get("reason"), row["path"])
                if row.get("destination", {}).get("path") == "evals/teamwork/migrations/v3-case-replacements.json":
                    replacements = json.loads(
                        (REPO_ROOT / "evals/teamwork/migrations/v3-case-replacements.json").read_text()
                    )
                    covered = {
                        source for group in replacements["groups"] for source in group["sources"]
                    }
                    self.assertIn(pathlib.PurePosixPath(row["path"]).name, covered, row["path"])
        aba = next(row for row in records if row.get("path") == "scripts/tests/test_init_project_aba.py" and row["record_type"] == "candidate-path")
        self.assertNotEqual(aba["disposition"], "retire")
        if aba["observed_status"] == "D":
            self.assertEqual(aba["disposition"], "restore")
            self.assertEqual(aba["destination"]["owner"], "W5-init")
        judge = next(row for row in records if row.get("path") == "templates/codex-agents/teamwork-judge.toml" and row["record_type"] == "candidate-path")
        self.assertEqual(judge["observed_status"], "D")
        self.assertEqual(judge["disposition"], "retire")
        self.assertEqual(judge["retirement"]["accepted_plan"], PLAN)

    def test_forbidden_and_index_snapshots_rehash_and_fail_closed_on_drift(self) -> None:
        metadata, records = self.ledger[0], self.ledger[1:]
        self.assertEqual(metadata["snapshot_algorithms"], self.inventory["snapshot_algorithms"])
        forbidden_rows = [row for row in records if row["record_type"] == "forbidden-snapshot"]
        self.assertEqual(len(forbidden_rows), 1)
        forbidden = forbidden_rows[0]
        forbidden_root = REPO_ROOT / ".claude"
        if os.environ.get("TEAMWORK_CANDIDATE_ISOLATED") == "1":
            # The candidate transaction intentionally excludes user-owned
            # forbidden paths; its wrapper rehashes them before and after this
            # isolated run, so this test must not fabricate that tree.
            self.assertFalse(forbidden_root.exists())
            self.assertEqual(forbidden["preimage"]["file_type"], "directory")
        else:
            expected_tree = {"file_type": "directory", "mode": mode_of(forbidden_root), "sha256": tree_sha256(forbidden_root)}
            self.assertEqual(forbidden["preimage"], expected_tree)
        if os.environ.get("TEAMWORK_CANDIDATE_ISOLATED") == "1":
            return
        index_rows = [row for row in records if row["record_type"] == "git-index"]
        self.assertEqual(len(index_rows), 1)
        index = index_rows[0]
        actual_index = index_snapshot()
        self.assertEqual(index["preimage"], {key: actual_index[key] for key in ("file_type", "mode", "sha256")})
        self.assertEqual(index["index_snapshot"], {key: actual_index[key] for key in actual_index if key not in {"file_type", "mode", "sha256"}})
        self.assertEqual(
            set(index["preimage"]) | set(index["index_snapshot"]),
            set(metadata["snapshot_algorithms"]["git-index-v1"]["required_fields"]),
        )
        self.assertEqual(
            actual_index["intent_to_add"],
            [
                {"path": "scripts/tests/fixtures/v3.4.2-skill-inventory.json", "flags": "20004000"},
                {"path": "scripts/tests/test_v342_skill_upgrade.py", "flags": "20004000"},
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            temp = pathlib.Path(directory)
            nested = temp / "nested"
            nested.mkdir()
            leaf = nested / "fixture.txt"
            leaf.write_text("before", encoding="utf-8")
            before = tree_sha256(temp)
            leaf.write_text("after", encoding="utf-8")
            self.assertNotEqual(before, tree_sha256(temp))
            file_before = hashlib.sha256(b"before").hexdigest()
            self.assertNotEqual(file_before, hashlib.sha256(leaf.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
