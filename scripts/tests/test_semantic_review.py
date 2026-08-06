from __future__ import annotations

import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from teamwork_tooling.semantic_review import SemanticReviewError, release_readiness


def reviewer_evidence(**overrides):
    evidence = {
        "status": "PASS",
        "producer_identity": "installed-host-output",
        "reviewer": {
            "identity": "independent-reviewer-1",
            "role": "reviewer",
            "independent": True,
            "read_actual_candidate": True,
        },
        "verdict": "ACCEPT",
        "actual_candidate": {
            "path": "outputs/installed/codex/result.txt",
            "content_read": "Observed answer and scenario verification result.",
        },
        "outcome_rubric": {
            "question": "Did the observed result satisfy the requested public behavior?",
            "outcomes": ["correct result", "honest evidence boundary"],
        },
        "review": "The actual output satisfies both outcomes without unsupported claims.",
    }
    evidence.update(overrides)
    return evidence


class ReleaseEvidenceLaneTests(unittest.TestCase):
    def test_all_required_lanes_pass(self) -> None:
        result = release_readiness({
            "structural": "PASS",
            "behavioral": "PASS",
            "semantic": reviewer_evidence(),
        })
        self.assertEqual("release-ready", result["status"])
        self.assertEqual({}, result["blockers"])

    def test_missing_or_unsupported_required_lane_blocks(self) -> None:
        result = release_readiness({"structural": "PASS", "behavioral": "UNSUPPORTED"})
        self.assertEqual("not-release-ready", result["status"])
        self.assertEqual("UNSUPPORTED", result["blockers"]["behavioral"])
        self.assertEqual("NOT RUN", result["blockers"]["semantic"])

    def test_bare_semantic_pass_is_rejected(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "independent Reviewer"):
            release_readiness({"semantic": "PASS"})

    def test_semantic_pass_rejects_self_review_or_unread_candidate(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "self-review"):
            release_readiness({"semantic": reviewer_evidence(
                producer_identity="same-reviewer",
                reviewer={
                    "identity": "same_reviewer", "role": "reviewer",
                    "independent": True, "read_actual_candidate": True,
                },
            )})
        unread = reviewer_evidence()
        unread["reviewer"] = {**unread["reviewer"], "read_actual_candidate": False}
        with self.assertRaisesRegex(SemanticReviewError, "read the actual candidate"):
            release_readiness({"semantic": unread})

    def test_semantic_pass_requires_outcome_rubric_and_accept_verdict(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "outcome-based rubric"):
            release_readiness({"semantic": reviewer_evidence(outcome_rubric={})})
        with self.assertRaisesRegex(SemanticReviewError, "ACCEPT"):
            release_readiness({"semantic": reviewer_evidence(verdict="REVISE")})


if __name__ == "__main__":
    unittest.main()
