"""Release-evidence lane gate for Teamwork.

This module does not score prose or infer behavior from hashes.  It only keeps
the four evidence lanes distinct and prevents absent or unsupported evidence
from being reported as release-ready.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


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
INSTALLED_SEMANTIC_PASS_FIELDS = frozenset({
    "status", "producer_identity", "reviewer", "verdict", "prompt", "agent_output", "rubric", "binding",
})
INSTALLED_SEMANTIC_BINDING_FIELDS = frozenset({
    "prompt_sha256", "agent_output_sha256", "rubric_sha256",
})


class SemanticReviewError(ValueError):
    """Raised when release-lane evidence has an invalid shape or value."""


def _sha256_value(value: Any) -> str:
    if isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticReviewError(f"installed_semantic {label} must be a non-empty string")
    return value


def _normalized_identity(value: str) -> str:
    return " ".join(value.casefold().replace("_", "-").split())


def _validate_installed_semantic_reviewer(value: Any, producer_identity: str) -> None:
    if not isinstance(value, Mapping):
        raise SemanticReviewError("installed_semantic reviewer must be a mapping")
    required = {"identity", "role", "independent"}
    if set(value) != required:
        raise SemanticReviewError("installed_semantic reviewer must bind identity, role, and independence")
    identity = _nonempty_string(value.get("identity"), "reviewer.identity")
    role = _nonempty_string(value.get("role"), "reviewer.role").casefold().replace("_", "-")
    if role not in {"reviewer", "teamwork-reviewer"}:
        raise SemanticReviewError("installed_semantic PASS requires Reviewer evidence")
    if value.get("independent") is not True:
        raise SemanticReviewError("installed_semantic PASS requires an independent Reviewer")
    normalized_identity = _normalized_identity(identity)
    if normalized_identity in {"self", "root", "author", "candidate", "worker"}:
        raise SemanticReviewError("installed_semantic PASS rejects self-review evidence")
    if normalized_identity == _normalized_identity(producer_identity):
        raise SemanticReviewError("installed_semantic PASS rejects self-review evidence")


def _validate_installed_semantic_pass(value: Any) -> str:
    if isinstance(value, str):
        if value == "PASS":
            raise SemanticReviewError("installed_semantic PASS requires structured independent Reviewer evidence")
        if value not in RELEASE_LANE_STATUSES:
            raise SemanticReviewError(f"invalid release evidence lane statuses: {{'installed_semantic': {value!r}}}")
        return value
    if not isinstance(value, Mapping):
        raise SemanticReviewError("installed_semantic evidence must be a status or structured mapping")
    if set(value) != INSTALLED_SEMANTIC_PASS_FIELDS:
        raise SemanticReviewError("installed_semantic evidence must bind reviewer, verdict, prompt, output, and rubric")
    status = value.get("status")
    if status not in RELEASE_LANE_STATUSES:
        raise SemanticReviewError(f"invalid release evidence lane statuses: {{'installed_semantic': {status!r}}}")
    if status != "PASS":
        return str(status)
    if value.get("verdict") != "PASS":
        raise SemanticReviewError("installed_semantic PASS requires a PASS Reviewer verdict")
    producer_identity = _nonempty_string(value.get("producer_identity"), "producer_identity")
    _validate_installed_semantic_reviewer(value.get("reviewer"), producer_identity)
    prompt = _nonempty_string(value.get("prompt"), "prompt")
    agent_output = _nonempty_string(value.get("agent_output"), "agent_output")
    rubric = value.get("rubric")
    if rubric is None or (isinstance(rubric, str) and not rubric.strip()):
        raise SemanticReviewError("installed_semantic rubric must be present")
    binding = value.get("binding")
    if not isinstance(binding, Mapping) or set(binding) != INSTALLED_SEMANTIC_BINDING_FIELDS:
        raise SemanticReviewError("installed_semantic binding must include prompt, agent_output, and rubric digests")
    expected = {
        "prompt_sha256": _sha256_value(prompt),
        "agent_output_sha256": _sha256_value(agent_output),
        "rubric_sha256": _sha256_value(rubric),
    }
    if any(binding.get(key) != digest for key, digest in expected.items()):
        raise SemanticReviewError("installed_semantic binding digest does not match prompt, agent_output, or rubric")
    return "PASS"


def release_readiness(lanes: Mapping[str, Any]) -> dict[str, object]:
    """Return the release gate without upgrading missing evidence to success."""

    if not isinstance(lanes, Mapping):
        raise SemanticReviewError("release evidence lanes must be a mapping")
    unknown = sorted(set(lanes) - set(RELEASE_EVIDENCE_LANES))
    if unknown:
        raise SemanticReviewError(f"unknown release evidence lanes: {unknown}")
    normalized: dict[str, str] = {}
    for lane in RELEASE_EVIDENCE_LANES:
        value = lanes.get(lane, "NOT RUN")
        if lane == "installed_semantic":
            normalized[lane] = _validate_installed_semantic_pass(value)
            continue
        if not isinstance(value, str) or value not in RELEASE_LANE_STATUSES:
            raise SemanticReviewError(f"invalid release evidence lane statuses: {{{lane!r}: {value!r}}}")
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
