from __future__ import annotations

import hashlib
import json
import unittest

from teamwork_tooling.semantic_review import SemanticReviewError, release_readiness


def digest(value):
    if isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def reviewer_evidence(**overrides):
    prompt = "Use installed Research and answer from the scenario."
    agent_output = "The final answer cites a public source and preserves the private boundary."
    rubric = {"required": ["source quality", "privacy boundary"], "verdicts": ["PASS", "FAIL"]}
    evidence = {
        "status": "PASS",
        "producer_identity": "installed-host-candidate",
        "reviewer": {
            "identity": "teamwork-reviewer-live-1",
            "role": "reviewer",
            "independent": True,
        },
        "verdict": "PASS",
        "prompt": prompt,
        "agent_output": agent_output,
        "rubric": rubric,
        "binding": {
            "prompt_sha256": digest(prompt),
            "agent_output_sha256": digest(agent_output),
            "rubric_sha256": digest(rubric),
        },
    }
    evidence.update(overrides)
    return evidence


class ReleaseEvidenceLaneTests(unittest.TestCase):
    def test_all_required_lanes_pass(self) -> None:
        result = release_readiness({
            "static": "PASS",
            "installed_semantic": reviewer_evidence(),
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

    def test_installed_semantic_bare_pass_is_rejected(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "structured independent Reviewer evidence"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": "PASS",
                "disposable_write": "PASS",
            })

    def test_installed_semantic_requires_independent_reviewer_identity(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "Reviewer evidence"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": reviewer_evidence(
                    reviewer={"identity": "worker-1", "role": "worker", "independent": True},
                ),
                "disposable_write": "PASS",
            })
        with self.assertRaisesRegex(SemanticReviewError, "independent Reviewer"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": reviewer_evidence(
                    reviewer={"identity": "teamwork-reviewer-live-1", "role": "reviewer", "independent": False},
                ),
                "disposable_write": "PASS",
            })
        with self.assertRaisesRegex(SemanticReviewError, "self-review"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": reviewer_evidence(
                    reviewer={"identity": "self", "role": "reviewer", "independent": True},
                ),
                "disposable_write": "PASS",
            })
        with self.assertRaisesRegex(SemanticReviewError, "self-review"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": reviewer_evidence(
                    producer_identity="same-human-reviewer",
                    reviewer={"identity": "same_human_reviewer", "role": "reviewer", "independent": True},
                ),
                "disposable_write": "PASS",
            })

    def test_installed_semantic_requires_verdict_and_binding(self) -> None:
        missing_verdict = reviewer_evidence()
        del missing_verdict["verdict"]
        with self.assertRaisesRegex(SemanticReviewError, "bind reviewer, verdict"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": missing_verdict,
                "disposable_write": "PASS",
            })

        missing_binding = reviewer_evidence()
        del missing_binding["binding"]
        with self.assertRaisesRegex(SemanticReviewError, "bind reviewer, verdict"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": missing_binding,
                "disposable_write": "PASS",
            })

        with self.assertRaisesRegex(SemanticReviewError, "PASS Reviewer verdict"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": reviewer_evidence(verdict="FAIL"),
                "disposable_write": "PASS",
            })

    def test_installed_semantic_rejects_digest_mismatch(self) -> None:
        evidence = reviewer_evidence()
        evidence["binding"] = {**evidence["binding"], "agent_output_sha256": "0" * 64}
        with self.assertRaisesRegex(SemanticReviewError, "digest does not match"):
            release_readiness({
                "static": "PASS",
                "installed_semantic": evidence,
                "disposable_write": "PASS",
            })

    def test_non_mapping_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(SemanticReviewError, "must be a mapping"):
            release_readiness([])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
