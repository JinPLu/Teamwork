#!/usr/bin/env python3
"""C5 scope allowlist and exact-one-owner tests."""

from __future__ import annotations

import json
import pathlib
import subprocess
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
ALLOWLIST_PATH = REPO_ROOT / "evals/teamwork/manifests/v4.1.0-teamwork-c5-scope-allowlist.json"
OWNERSHIP_PATH = FIXTURES / "v4.1.0-teamwork-c5-path-ownership.json"

BASE_COMMIT = "39de72f326ca68bc3a84a957794adfa76913b674"
CANDIDATE_ID = "teamwork-4.1.0-c5"
HISTORICAL_VERSION = "4.1.0"
PLAN_SHA256 = "79dfe3db4141df6fb460d9d1ad4a5604f68470ddf599de0caab40d3eb5b48dfc"
ACCEPTED_PLAN_REVIEW_SHA256 = "607d167a2ac6e94f3b2b206c7af0d3affdf84bfaf7a47e45c99956144672e857"
ACCEPTED_PLAN_REVIEW_PAYLOAD_SHA256 = "b745716604ecff603a5565cdc5a49baa590ccb93c60d35ec157ce8db7bf2717e"

GUARANTEED_DELTA_PATHS = [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "VERSION",
    "evals/teamwork/ledgers/v4.1.0-teamwork-c5.jsonl",
    "evals/teamwork/manifests/v4.1.0-teamwork-c5-cases.json",
    "evals/teamwork/manifests/v4.1.0-teamwork-c5-paths.json",
    "evals/teamwork/manifests/v4.1.0-teamwork-c5-scope-allowlist.json",
    "evals/teamwork/reviews/v4.1.0-teamwork-c5.json",
    "evals/teamwork/validation/v4.1.0-teamwork-c5.json",
    "plugins/teamwork-skill/.codex-plugin/plugin.json",
    "plugins/teamwork-skill/VERSION",
]

W0_PATHS = {
    "evals/teamwork/manifests/v4.1.0-teamwork-c5-scope-allowlist.json",
    "scripts/tests/fixtures/v4.1.0-teamwork-c5-path-ownership.json",
    "scripts/tests/test_v4_path_ownership.py",
    "scripts/tests/test_v410_teamwork_ledger.py",
}
RUNTIME_PATHS = {
    "evals/teamwork/ledgers/v4.1.0-teamwork-c5.jsonl",
    "evals/teamwork/manifests/v4.1.0-teamwork-c5-paths.json",
    "evals/teamwork/reviews/v4.1.0-teamwork-c5.json",
    "evals/teamwork/validation/v4.1.0-teamwork-c5.json",
}
SHARED_REQUIRED = {
    "scripts/test_codex_routing_config.py",
    "scripts/validation/integration.sh",
    "scripts/tests/test_skill_topology_v4.py",
    "scripts/tests/test_policy_contract_v4.py",
    "scripts/tests/test_evaluation_contract_v4.py",
}


def read_json(path: pathlib.Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} root is not a JSON object")
    return value


def dirty_paths() -> list[str]:
    raw = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=REPO_ROOT,
    ).split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(raw):
        record = raw[index]
        index += 1
        if not record:
            continue
        text = record.decode("utf-8")
        status = text[:2]
        path = text[3:]
        if status.startswith(("R", "C")) and index < len(raw):
            path = raw[index].decode("utf-8")
            index += 1
        if not path.startswith(".claude/"):
            paths.append(path)
    return sorted(set(paths), key=lambda value: value.encode("utf-8"))


class C5PathOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.allowlist = read_json(ALLOWLIST_PATH)
        cls.ownership = read_json(OWNERSHIP_PATH)

    def test_allowlist_is_current_dirty_delta_plus_guaranteed_c5_paths(self) -> None:
        current_version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        if current_version != HISTORICAL_VERSION:
            self.skipTest("the c5 dirty-delta snapshot only applies to Teamwork 4.1.0")
        expected = sorted(set(dirty_paths()) | set(GUARANTEED_DELTA_PATHS), key=lambda value: value.encode("utf-8"))
        self.assertEqual(self.allowlist["allowed_paths"], expected)
        self.assertEqual(self.allowlist["guaranteed_delta_paths"], GUARANTEED_DELTA_PATHS)
        for path in self.allowlist["allowed_paths"]:
            self.assertNotIn("*", path)
            self.assertNotIn("?", path)
            self.assertNotIn("c4", path)
            self.assertFalse(path.startswith(".claude/"))
        self.assertTrue(set(W0_PATHS) <= set(self.allowlist["allowed_paths"]))
        self.assertTrue(set(RUNTIME_PATHS) <= set(self.allowlist["allowed_paths"]))

    def test_allowlist_binds_c5_review_and_plan_inputs(self) -> None:
        self.assertEqual(
            set(self.allowlist),
            {
                "schema_version",
                "base_commit",
                "candidate_id",
                "reviewed_plan_sha256",
                "accepted_plan_review_sha256",
                "accepted_plan_review_payload_sha256",
                "design_bindings",
                "plan_bindings",
                "guaranteed_delta_paths",
                "allowed_paths",
                "owners",
            },
        )
        self.assertEqual(self.allowlist["schema_version"], 1)
        self.assertEqual(self.allowlist["base_commit"], BASE_COMMIT)
        self.assertEqual(self.allowlist["candidate_id"], CANDIDATE_ID)
        self.assertEqual(self.allowlist["reviewed_plan_sha256"], PLAN_SHA256)
        self.assertEqual(self.allowlist["accepted_plan_review_sha256"], ACCEPTED_PLAN_REVIEW_SHA256)
        self.assertEqual(self.allowlist["accepted_plan_review_payload_sha256"], ACCEPTED_PLAN_REVIEW_PAYLOAD_SHA256)
        self.assertEqual(
            self.allowlist["plan_bindings"]["plan2"]["sha256"],
            "7dfde7a69a58a80ca7c4cba3ab9372d3ee1e4cf10999e3f2b0571569c0e9a478",
        )
        self.assertEqual(
            self.allowlist["design_bindings"]["design2_current_migrated"]["file_sha256"],
            "2fde45dd132df3eeefc203718532a052a7615bb04264540dd4075d830d723889",
        )

    def test_every_allowed_path_has_exactly_one_existing_worker_owner(self) -> None:
        self.assertEqual(self.ownership["schema_version"], 1)
        self.assertEqual(self.ownership["base_commit"], BASE_COMMIT)
        self.assertEqual(self.ownership["candidate_id"], CANDIDATE_ID)
        self.assertEqual(self.ownership["default_owner"], "FORBIDDEN")
        self.assertEqual(self.ownership["forbidden_prefixes"], [".claude/"])
        self.assertEqual(set(self.ownership["owners"]), set(self.allowlist["allowed_paths"]))
        self.assertEqual(self.allowlist["owners"], self.ownership["owners"])
        for path, owner in self.ownership["owners"].items():
            self.assertIsInstance(owner, str)
            self.assertTrue(owner.startswith("W-") or owner.startswith("W0-"), (path, owner))

    def test_named_owner_boundaries_are_not_ambiguous(self) -> None:
        owners = self.ownership["owners"]
        for path in W0_PATHS:
            self.assertEqual(owners[path], "W0-scope-freeze")
        for path in RUNTIME_PATHS:
            self.assertEqual(owners[path], "W-runtime-release")
        for path in SHARED_REQUIRED:
            self.assertEqual(owners[path], "W-shared-integration")
        self.assertEqual(
            owners["evals/teamwork/manifests/v4.1.0-teamwork-c5-paths.json"],
            "W-runtime-release",
        )


if __name__ == "__main__":
    unittest.main()
