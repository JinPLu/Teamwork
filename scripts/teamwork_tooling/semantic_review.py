"""Keep structural, behavioral, and semantic release evidence distinct."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


RELEASE_EVIDENCE_LANES = ("structural", "behavioral", "semantic", "dry_run")
REQUIRED_RELEASE_EVIDENCE_LANES = ("structural", "behavioral", "semantic")
RELEASE_LANE_STATUSES = frozenset({"PASS", "FAIL", "UNSUPPORTED", "NOT RUN"})


class SemanticReviewError(ValueError):
    """Raised when release evidence has an invalid shape or claim."""


def _nonempty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticReviewError(f"semantic {label} must be non-empty text")
    return value


def _normalized_identity(value: str) -> str:
    return " ".join(value.casefold().replace("_", "-").split())


def _semantic_status(value: Any) -> str:
    if isinstance(value, str):
        if value == "PASS":
            raise SemanticReviewError("semantic PASS requires an independent Reviewer reading the actual candidate")
        if value not in RELEASE_LANE_STATUSES:
            raise SemanticReviewError(f"invalid semantic evidence status: {value!r}")
        return value
    if not isinstance(value, Mapping):
        raise SemanticReviewError("semantic evidence must be a status or mapping")
    status = value.get("status")
    if status not in RELEASE_LANE_STATUSES:
        raise SemanticReviewError(f"invalid semantic evidence status: {status!r}")
    if status != "PASS":
        return str(status)

    producer = _nonempty_text(value.get("producer_identity"), "producer_identity")
    reviewer = value.get("reviewer")
    if not isinstance(reviewer, Mapping):
        raise SemanticReviewError("semantic PASS requires Reviewer evidence")
    identity = _nonempty_text(reviewer.get("identity"), "reviewer.identity")
    role = _nonempty_text(reviewer.get("role"), "reviewer.role").casefold().replace("_", "-")
    if role not in {"reviewer", "teamwork-reviewer"}:
        raise SemanticReviewError("semantic PASS requires the Reviewer role")
    if reviewer.get("independent") is not True:
        raise SemanticReviewError("semantic PASS requires an independent Reviewer")
    if reviewer.get("read_actual_candidate") is not True:
        raise SemanticReviewError("semantic PASS requires the Reviewer to read the actual candidate")
    if _normalized_identity(identity) in {"self", "root", "author", "candidate", "worker"}:
        raise SemanticReviewError("semantic PASS rejects self-review")
    if _normalized_identity(identity) == _normalized_identity(producer):
        raise SemanticReviewError("semantic PASS rejects self-review")

    actual = value.get("actual_candidate")
    if not isinstance(actual, Mapping):
        raise SemanticReviewError("semantic PASS requires the actual candidate path and content read")
    _nonempty_text(actual.get("path"), "actual_candidate.path")
    _nonempty_text(actual.get("content_read"), "actual_candidate.content_read")
    _nonempty_text(value.get("review"), "review")
    rubric = value.get("outcome_rubric")
    if not isinstance(rubric, Mapping) or not rubric:
        raise SemanticReviewError("semantic PASS requires an outcome-based rubric")
    if value.get("verdict") != "ACCEPT":
        raise SemanticReviewError("semantic PASS requires an ACCEPT Reviewer verdict")
    return "PASS"


def release_readiness(lanes: Mapping[str, Any]) -> dict[str, object]:
    """Return readiness without upgrading missing or unsupported evidence."""

    if not isinstance(lanes, Mapping):
        raise SemanticReviewError("release evidence lanes must be a mapping")
    unknown = sorted(set(lanes) - set(RELEASE_EVIDENCE_LANES))
    if unknown:
        raise SemanticReviewError(f"unknown release evidence lanes: {unknown}")
    normalized: dict[str, str] = {}
    for lane in RELEASE_EVIDENCE_LANES:
        value = lanes.get(lane, "NOT RUN")
        if lane == "semantic":
            normalized[lane] = _semantic_status(value)
        elif not isinstance(value, str) or value not in RELEASE_LANE_STATUSES:
            raise SemanticReviewError(f"invalid release evidence status for {lane}: {value!r}")
        else:
            normalized[lane] = value
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
