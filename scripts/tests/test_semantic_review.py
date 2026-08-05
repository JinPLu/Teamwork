from __future__ import annotations

import unittest

from teamwork_tooling.semantic_review import SemanticReviewError, release_readiness


class ReleaseEvidenceLaneTests(unittest.TestCase):
    def test_all_required_lanes_pass(self) -> None:
        result = release_readiness({
            "static": "PASS",
            "installed_semantic": "PASS",
            "disposable_write": "PASS",
        })
        self.assertEqual("release-ready", result["status"])
        self.assertEqual({}, result["blockers"])
        self.assertEqual("NOT RUN", result["lanes"]["dry_run"])

    def test_dry_run_never_substitutes_for_semantic_evidence(self) -> None:
        result = release_readiness({"static": "PASS", "dry_run": "PASS"})
        self.assertEqual("not-release-ready", result["status"])
        self.assertEqual("NOT RUN", result["blockers"]["installed_semantic"])
        self.assertEqual("NOT RUN", result["blockers"]["disposable_write"])

    def test_required_fail_unsupported_and_not_run_are_blockers(self) -> None:
        result = release_readiness({
            "static": "FAIL",
            "installed_semantic": "UNSUPPORTED",
            "disposable_write": "NOT RUN",
            "dry_run": "PASS",
        })
        self.assertEqual({
            "static": "FAIL",
            "installed_semantic": "UNSUPPORTED",
            "disposable_write": "NOT RUN",
        }, result["blockers"])

    def test_unknown_lane_and_status_are_rejected(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "unknown release evidence lanes"):
            release_readiness({"semantic-ish": "PASS"})
        with self.assertRaisesRegex(SemanticReviewError, "invalid release evidence lane statuses"):
            release_readiness({"static": "SKIPPED"})

    def test_non_mapping_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "must be a mapping"):
            release_readiness([])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
