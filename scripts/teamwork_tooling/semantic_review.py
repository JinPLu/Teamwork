"""Release-evidence lane gate for Teamwork.

This module does not score prose or infer behavior from hashes.  It only keeps
the four evidence lanes distinct and prevents absent or unsupported evidence
from being reported as release-ready.
"""

from __future__ import annotations

from collections.abc import Mapping


RELEASE_EVIDENCE_LANES = (
    "static",
    "installed_semantic",
    "disposable_write",
    "dry_run",
)
REQUIRED_RELEASE_EVIDENCE_LANES = (
    "static",
    "installed_semantic",
    "disposable_write",
)
RELEASE_LANE_STATUSES = frozenset({"PASS", "FAIL", "UNSUPPORTED", "NOT RUN"})


class SemanticReviewError(ValueError):
    """Raised when release-lane evidence has an invalid shape or value."""


def release_readiness(lanes: Mapping[str, str]) -> dict[str, object]:
    """Return the release gate without upgrading missing evidence to success."""

    if not isinstance(lanes, Mapping):
        raise SemanticReviewError("release evidence lanes must be a mapping")
    unknown = sorted(set(lanes) - set(RELEASE_EVIDENCE_LANES))
    if unknown:
        raise SemanticReviewError(f"unknown release evidence lanes: {unknown}")
    invalid = {
        lane: status
        for lane, status in lanes.items()
        if not isinstance(status, str) or status not in RELEASE_LANE_STATUSES
    }
    if invalid:
        raise SemanticReviewError(f"invalid release evidence lane statuses: {invalid}")

    normalized = {
        lane: lanes.get(lane, "NOT RUN")
        for lane in RELEASE_EVIDENCE_LANES
    }
    blockers = {
        lane: normalized[lane]
        for lane in REQUIRED_RELEASE_EVIDENCE_LANES
        if normalized[lane] != "PASS"
    }
    return {
        "status": "release-ready" if not blockers else "not-release-ready",
        "lanes": normalized,
        "blockers": blockers,
    }
