#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_teamwork_index import ValidationError, validate_discussion_artifact_text  # noqa: E402


class DiscussionArtifactSchemaTests(unittest.TestCase):
    def artifact(self, *, status: str = "active", title: str = "Choose the release evidence boundary") -> str:
        return f"""Artifact Type: discussion
Status: {status}
Authority: supporting
Last Updated: 2026-07-15
Search Keys: release, evidence, handoff
Abstract: Preserve the evidence-boundary decision for the next maintainer.
Linked Artifacts: none
Superseded By: none

# {title}

## Goal

Choose evidence sufficient to release without expanding the public contract.

## Settled

- Keep validation and release review because both directly cover the contract.
- Keep the current branch because isolation is not required.

## Still open

- Decide whether the platform smoke test adds evidence beyond validation.

## Key evidence

- The release policy requires validation and fresh review before publishing.

## Continue here

Compare the platform smoke test with validation, then decide whether to run it.
"""

    def validate(self, text: str, *, status: str = "active") -> None:
        validate_discussion_artifact_text(
            text,
            expected_status=status,
            expected_updated="2026-07-15",
        )

    def test_human_readable_artifact_without_diagram_is_valid(self) -> None:
        self.validate(self.artifact())

    def test_old_generic_title_and_old_required_sections_are_invalid(self) -> None:
        with self.assertRaisesRegex(ValidationError, "H1 title must be specific"):
            self.validate(self.artifact(title="Teamwork Discussion"))

        old_sections = self.artifact().replace("## Goal", "## Starting Question")
        with self.assertRaisesRegex(ValidationError, "missing section: Goal"):
            self.validate(old_sections)

    def test_active_still_open_cannot_be_none(self) -> None:
        active = self.artifact().replace(
            "- Decide whether the platform smoke test adds evidence beyond validation.",
            "None.",
        )
        with self.assertRaisesRegex(ValidationError, "Still open must name an unresolved item"):
            self.validate(active)

        accepted = active.replace("Status: active", "Status: accepted")
        self.validate(accepted, status="accepted")

    def test_rejects_statuses_outside_the_discussion_body_protocol(self) -> None:
        for status in ("blocked", "historical", "candidate"):
            with self.subTest(status=status):
                artifact = self.artifact().replace("Status: active", f"Status: {status}")
                with self.assertRaisesRegex(ValidationError, "Status has unknown value"):
                    self.validate(artifact, status=status)

    def test_optional_decision_map_accepts_a_basic_flowchart(self) -> None:
        artifact = self.artifact() + """

## Decision map

```mermaid
flowchart LR
    release[Release evidence] --> smoke[Platform smoke test]
```
"""
        self.validate(artifact)

        invalid = artifact.replace("flowchart LR", "sequenceDiagram")
        with self.assertRaisesRegex(ValidationError, "Decision map must be a flowchart"):
            self.validate(invalid)


if __name__ == "__main__":
    unittest.main()
