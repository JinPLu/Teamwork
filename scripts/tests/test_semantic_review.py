from __future__ import annotations

import json
import unittest
from pathlib import Path

from teamwork_tooling.semantic_review import (
    SemanticReviewError,
    message_sha256,
    trajectory_sha256,
    validate_accepted_ledger_v2,
    validate_semantic_review,
)


ROOT = Path(__file__).resolve().parents[2]
RUBRIC = json.loads(
    (ROOT / "evals/teamwork/rubrics/teamwork-live-semantic-v1.json").read_text(
        encoding="utf-8"
    )
)


def sample_trajectory() -> dict[str, object]:
    return {
        "schema_version": 5,
        "record_type": "teamwork_live_trajectory",
        "run_id": "run-001",
        "turns": [
            {
                "prompt": "$grill-me review this public compatibility change.",
                "final_output": "Should the public default remain compatible?",
                "raw_events": [
                    {"type": "thread.started"},
                    {"type": "item.completed", "item": {"type": "agent_message"}},
                ],
            },
            {
                "prompt": "Yes, preserve compatibility.",
                "final_output": "The decision is resolved; no implementation was authorized.",
                "raw_events": [{"type": "item.completed"}],
            },
        ],
    }


def evidence(turn: int = 1, event: int | None = None) -> list[dict[str, int]]:
    reference = {"turn": turn}
    if event is not None:
        reference["event"] = event
    return [reference]


def sample_review(verdict: str = "ACCEPT") -> dict[str, object]:
    trajectory = sample_trajectory()
    outcomes = ["PASS"] * len(RUBRIC["criteria"])
    outcomes[0] = {
        "ACCEPT": "PASS",
        "REVISE": "REVISE",
        "REJECT": "FAIL",
        "INCONCLUSIVE": "INCONCLUSIVE",
    }[verdict]
    scores = {
        "PASS": 4,
        "REVISE": 2,
        "FAIL": 0,
        "INCONCLUSIVE": 1,
    }
    return {
        "schema_version": 1,
        "run_id": "run-001",
        "trajectory_sha256": trajectory_sha256(trajectory),
        "rubric_id": "teamwork-live-semantic-v1",
        "reviewer": {
            "kind": "MODEL",
            "identity": "reviewer-example",
            "version": "2026-07-15",
        },
        "verdict": verdict,
        "criteria": [
            {
                "criterion_id": criterion["id"],
                "outcome": outcome,
                "score": scores[outcome],
                "evidence": evidence(1, 2),
            }
            for criterion, outcome in zip(RUBRIC["criteria"], outcomes)
        ],
        "activation_evidence": {
            "claim": "AVAILABILITY_ONLY",
            "sources": [
                {
                    "kind": "INSTALLED_FILE",
                    "path": ".agents/skills/grill-me/SKILL.md",
                    "sha256": "a" * 64,
                }
            ],
        },
        "rationale": "The cited turns support the criterion outcomes and verdict.",
        "confidence": 0.85,
        "timestamp": "2026-07-15T10:30:00Z",
    }


def accepted_ledger_v2_entry(claim_type: str = "SOURCE_PARITY", lane: str = "STATIC_OFFLINE") -> dict[str, object]:
    provenance: dict[str, object] = {
        "package_version": "3.4.0",
        "source_sha256": "a" * 64,
    }
    if lane == "HELPER_BLACK_BOX":
        provenance["helper_test_sha256"] = "b" * 64
    if lane == "LIVE":
        provenance.update(
            {
                "host": "codex",
                "model": "test-model",
                "config_sha256": "c" * 64,
                "prompt_sha256": "d" * 64,
                "repeats": 2,
                "trajectory_sha256": "e" * 64,
                "review_sha256": "f" * 64,
            }
        )
    if claim_type == "AUTOMATIC_ACTIVATION":
        provenance["host_activation_event"] = {
            "trajectory_sha256": "e" * 64,
            "event": 1,
        }
    return {
        "schema_version": 2,
        "package_version": "3.4.0",
        "behavior_claims": [
            {
                "type": claim_type,
                "evidence_lane": lane,
                "claim_limits": ["Bounded to recorded evidence."],
                "provenance": provenance,
            }
        ],
    }


class SemanticReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trajectory = sample_trajectory()

    def assert_invalid(self, review: dict[str, object], message: str) -> None:
        with self.assertRaisesRegex(SemanticReviewError, message):
            validate_semantic_review(review, self.trajectory, RUBRIC)

    def test_accepts_grounded_verdict_variants(self) -> None:
        for verdict in ("ACCEPT", "REVISE", "REJECT", "INCONCLUSIVE"):
            with self.subTest(verdict=verdict):
                validate_semantic_review(sample_review(verdict), self.trajectory, RUBRIC)

    def test_accepts_message_hash_and_stronger_explicit_activation_evidence(self) -> None:
        review = sample_review()
        review["criteria"][0]["evidence"] = [
            {
                "message_sha256": message_sha256(
                    "$grill-me review this public compatibility change."
                )
            }
        ]
        review["activation_evidence"] = {
            "claim": "EXPLICIT_ACTIVATION",
            "sources": [
                {"kind": "EXPLICIT_INVOCATION", "evidence": evidence(1)}
            ],
        }
        validate_semantic_review(review, self.trajectory, RUBRIC)

    def test_accepts_automatic_activation_only_with_host_event_evidence(self) -> None:
        review = sample_review()
        review["activation_evidence"] = {
            "claim": "AUTOMATIC_ACTIVATION",
            "sources": [
                {"kind": "HOST_ACTIVATION_EVENT", "evidence": evidence(1, 1)}
            ],
        }
        validate_semantic_review(review, self.trajectory, RUBRIC)

    def test_rejects_missing_required_field_and_unknown_values(self) -> None:
        review = sample_review()
        del review["confidence"]
        self.assert_invalid(review, "missing fields: confidence")

        review = sample_review()
        review["verdict"] = "APPROVE"
        self.assert_invalid(review, "unknown verdict")

        review = sample_review()
        review["criteria"][0]["criterion_id"] = "made_up"
        self.assert_invalid(review, "unknown criteria: made_up")

    def test_rejects_missing_or_dangling_criterion_evidence(self) -> None:
        review = sample_review()
        review["criteria"][0]["evidence"] = []
        self.assert_invalid(review, "evidence must be a non-empty list")

        review = sample_review()
        review["criteria"][0]["evidence"] = evidence(3)
        self.assert_invalid(review, "turn 3 does not exist")

        review = sample_review()
        review["criteria"][0]["evidence"] = [{"message_sha256": "b" * 64}]
        self.assert_invalid(review, "message hash is not present")

    def test_rejects_trajectory_identity_mutations(self) -> None:
        review = sample_review()
        review["run_id"] = "other-run"
        self.assert_invalid(review, "run_id does not match")

        review = sample_review()
        review["trajectory_sha256"] = "0" * 64
        self.assert_invalid(review, "trajectory_sha256 does not match")

        review = sample_review()
        trajectory = sample_trajectory()
        trajectory["record_type"] = "authored_fixture"
        with self.assertRaisesRegex(SemanticReviewError, "trajectory record_type"):
            validate_semantic_review(review, trajectory, RUBRIC)

    def test_rejects_incomplete_criteria_and_verdict_outcome_mismatch(self) -> None:
        review = sample_review()
        review["criteria"].pop()
        self.assert_invalid(review, "missing criteria: mainline_question_value")

        review = sample_review("ACCEPT")
        review["criteria"][0].update({"outcome": "FAIL", "score": 0})
        self.assert_invalid(review, "ACCEPT requires every criterion to PASS")

        review = sample_review("INCONCLUSIVE")
        review["criteria"][0].update({"outcome": "PASS", "score": 4})
        self.assert_invalid(review, "INCONCLUSIVE requires")

    def test_rejects_unsafe_raw_prose_retention_anywhere(self) -> None:
        for field in ("raw_prompt", "raw_output", "transcript", "evidence_text"):
            with self.subTest(field=field):
                review = sample_review()
                review["criteria"][0][field] = "copied trajectory prose"
                self.assert_invalid(review, f"unsafe raw prose field.*{field}")

    def test_rejects_automatic_activation_claimed_from_installation_or_config(self) -> None:
        for source_kind in ("INSTALLED_FILE", "CONFIG"):
            with self.subTest(source_kind=source_kind):
                review = sample_review()
                source = {
                    "kind": source_kind,
                    "path": ".codex/config.toml",
                    "sha256": "c" * 64,
                }
                review["activation_evidence"] = {
                    "claim": "AUTOMATIC_ACTIVATION",
                    "sources": [source],
                }
                self.assert_invalid(
                    review,
                    "automatic activation requires HOST_ACTIVATION_EVENT evidence",
                )

    def test_rejects_score_and_timestamp_mutations(self) -> None:
        review = sample_review()
        review["criteria"][0]["score"] = 9
        self.assert_invalid(review, "score must be between 0 and 4")

        review = sample_review()
        review["timestamp"] = "2026-07-15 10:30:00"
        self.assert_invalid(review, "timestamp must be an RFC 3339 UTC timestamp")

        review = sample_review()
        review["confidence"] = True
        self.assert_invalid(review, "confidence must be a number")


class AcceptedLedgerV2Tests(unittest.TestCase):
    def test_accepts_matching_static_helper_and_live_provenance(self) -> None:
        static = accepted_ledger_v2_entry()
        helper = accepted_ledger_v2_entry("HELPER_BLACK_BOX", "HELPER_BLACK_BOX")
        live = accepted_ledger_v2_entry("EXPLICIT_ACTIVATION", "LIVE")
        validate_accepted_ledger_v2([{"date": "2026-07-15"}, static, helper, live])

    def test_rejects_v1_fallback_after_first_v2_row(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "must remain schema_version 2"):
            validate_accepted_ledger_v2([accepted_ledger_v2_entry(), {"date": "2026-07-16"}])

    def test_rejects_missing_or_mismatched_behavior_provenance(self) -> None:
        entry = accepted_ledger_v2_entry()
        claim = entry["behavior_claims"][0]
        claim["provenance"].pop("source_sha256")
        with self.assertRaisesRegex(SemanticReviewError, "requires source_sha256 or skill_manifest_sha256"):
            validate_accepted_ledger_v2([entry])

        entry = accepted_ledger_v2_entry()
        entry["behavior_claims"][0]["provenance"]["package_version"] = "3.3.0"
        with self.assertRaisesRegex(SemanticReviewError, "does not match ledger package_version"):
            validate_accepted_ledger_v2([entry])

    def test_rejects_claim_type_and_evidence_lane_mismatches(self) -> None:
        for claim_type, lane in (
            ("EXPLICIT_ACTIVATION", "STATIC_OFFLINE"),
            ("HELPER_BLACK_BOX", "STATIC_OFFLINE"),
            ("SOURCE_PARITY", "HELPER_BLACK_BOX"),
        ):
            with self.subTest(claim_type=claim_type, lane=lane):
                entry = accepted_ledger_v2_entry(claim_type, lane)
                with self.assertRaisesRegex(
                    SemanticReviewError, f"evidence_lane does not match {claim_type}"
                ):
                    validate_accepted_ledger_v2([entry])

    def test_rejects_live_claim_without_complete_live_provenance(self) -> None:
        entry = accepted_ledger_v2_entry("EXPLICIT_ACTIVATION", "LIVE")
        entry["behavior_claims"][0]["provenance"].pop("prompt_sha256")
        with self.assertRaisesRegex(SemanticReviewError, "missing live fields: prompt_sha256"):
            validate_accepted_ledger_v2([entry])

    def test_rejects_automatic_activation_without_host_event(self) -> None:
        entry = accepted_ledger_v2_entry("AUTOMATIC_ACTIVATION", "LIVE")
        entry["behavior_claims"][0]["provenance"].pop("host_activation_event")
        with self.assertRaisesRegex(SemanticReviewError, "automatic activation requires LIVE HOST_ACTIVATION_EVENT provenance"):
            validate_accepted_ledger_v2([entry])

    def test_rejects_host_event_bound_to_another_trajectory(self) -> None:
        entry = accepted_ledger_v2_entry("AUTOMATIC_ACTIVATION", "LIVE")
        entry["behavior_claims"][0]["provenance"]["host_activation_event"][
            "trajectory_sha256"
        ] = "0" * 64
        with self.assertRaisesRegex(
            SemanticReviewError, "host_activation_event trajectory does not match"
        ):
            validate_accepted_ledger_v2([entry])


if __name__ == "__main__":
    unittest.main()
