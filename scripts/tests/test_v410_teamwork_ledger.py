#!/usr/bin/env python3
"""W0 c5 release binding tests for the Teamwork 4.1.0 candidate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "scripts/release-index-transaction.py"
SPEC = importlib.util.spec_from_file_location("release_index_transaction", SOURCE)
assert SPEC and SPEC.loader
TX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TX)

PLAN = REPO_ROOT / "docs/teamwork/plans/2026-07-20-restore-mandatory-role-dispatch.md"
ALLOWLIST = REPO_ROOT / "evals/teamwork/manifests/v4.1.0-teamwork-c5-scope-allowlist.json"
OWNERSHIP = REPO_ROOT / "scripts/tests/fixtures/v4.1.0-teamwork-c5-path-ownership.json"
ACCEPTED_REVIEW = pathlib.Path("/tmp/teamwork-4.1.0-c5/accepted-plan-review.json")

PLAN_SHA256 = "79dfe3db4141df6fb460d9d1ad4a5604f68470ddf599de0caab40d3eb5b48dfc"
ACCEPTED_REVIEW_SHA256 = "607d167a2ac6e94f3b2b206c7af0d3affdf84bfaf7a47e45c99956144672e857"
CANDIDATE_ID = "teamwork-4.1.0-c5"
FINAL_DELTA_MANIFEST = "evals/teamwork/manifests/v4.1.0-teamwork-c5-paths.json"


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} root must be a JSON object")
    return value


def validate_w0_bindings(allowlist: dict, accepted_review: dict, accepted_review_sha256: str) -> None:
    if allowlist["reviewed_plan_sha256"] != PLAN_SHA256:
        raise AssertionError("W0 reviewed_plan_sha256 differs from the current Plan SHA")
    if accepted_review["plan_sha256"] != PLAN_SHA256:
        raise AssertionError("accepted Plan Review plan_sha256 differs from the current Plan SHA")
    if allowlist["accepted_plan_review_sha256"] != accepted_review_sha256:
        raise AssertionError("W0 accepted_plan_review_sha256 differs from the accepted review file SHA")
    if allowlist["accepted_plan_review_payload_sha256"] != accepted_review["review_payload_sha256"]:
        raise AssertionError("W0 accepted review payload binding differs from the accepted review payload")


def validate_final_delta_owner(ownership: dict) -> None:
    owner = ownership["owners"].get(FINAL_DELTA_MANIFEST)
    if owner != "W-runtime-release":
        raise AssertionError("final delta manifest must be owned by W-runtime-release")


class V410TeamworkLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.allowlist = read_json(ALLOWLIST)
        self.ownership = read_json(OWNERSHIP)
        self.accepted_review = read_json(ACCEPTED_REVIEW)

    def test_w0_currentness_bindings_match_plan_and_accepted_review(self) -> None:
        self.assertEqual(sha256_file(PLAN), PLAN_SHA256)
        self.assertEqual(sha256_file(ACCEPTED_REVIEW), ACCEPTED_REVIEW_SHA256)
        self.assertEqual(self.accepted_review["verdict"], "ACCEPT")
        self.assertEqual(self.accepted_review["candidate_id"], CANDIDATE_ID)
        validate_w0_bindings(self.allowlist, self.accepted_review, ACCEPTED_REVIEW_SHA256)

    def test_w0_bindings_fail_closed_on_plan_or_review_hash_drift(self) -> None:
        cases = (
            ("reviewed_plan_sha256", "allowlist", "reviewed_plan_sha256"),
            ("accepted plan_sha256", "accepted", "plan_sha256"),
            ("accepted_plan_review_sha256", "allowlist", "accepted_plan_review_sha256"),
            ("accepted payload sha256", "allowlist", "accepted_plan_review_payload_sha256"),
        )
        for label, target, field in cases:
            with self.subTest(label=label):
                allowlist = json.loads(json.dumps(self.allowlist))
                accepted = json.loads(json.dumps(self.accepted_review))
                if target == "accepted":
                    accepted[field] = "0" * 64
                else:
                    allowlist[field] = "0" * 64
                with self.assertRaises(AssertionError):
                    validate_w0_bindings(allowlist, accepted, ACCEPTED_REVIEW_SHA256)

    def test_final_delta_manifest_owner_fail_closed(self) -> None:
        validate_final_delta_owner(self.ownership)
        ownership = json.loads(json.dumps(self.ownership))
        ownership["owners"][FINAL_DELTA_MANIFEST] = "W-shared-integration"
        with self.assertRaisesRegex(AssertionError, "W-runtime-release"):
            validate_final_delta_owner(ownership)

    def test_release_transaction_c4_parser_exposes_hash_gate_arguments_when_available(self) -> None:
        parser = TX.parser()
        subcommands_action = next(
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        )
        choices = subcommands_action.choices
        if "freeze-ledger" not in choices:
            self.skipTest("freeze-ledger is implemented by the later release transaction slice")
        freeze_help = choices["freeze-ledger"].format_help()
        prepare_help = choices["prepare"].format_help()
        for expected in (
            "--plan-sha256",
            "--accepted-plan-review",
            "--accepted-plan-review-sha256",
            "--scope-allowlist",
            "--ownership",
            "--delta-manifest",
            "--design1-sha256",
            "--design2-pre-semantic-sha256",
            "--plan2-sha256",
        ):
            self.assertIn(expected, freeze_help)
        for expected in (
            "--scope-revision",
            "--accepted-plan-review",
            "--accepted-plan-review-sha256",
            "--ownership",
        ):
            self.assertIn(expected, prepare_help)


if __name__ == "__main__":
    unittest.main()
