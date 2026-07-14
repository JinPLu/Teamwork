"""Validation for external semantic reviews of recorded Teamwork trajectories.

The review artifact deliberately stores references and hashes, not copied prompt,
response, event, or transcript prose.  Structural live-run validation remains the
recorder's responsibility; this module checks the independently produced semantic
judgment against the exact recorded trajectory and an explicit rubric.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Mapping


SCHEMA_VERSION = 1
VERDICTS = {"ACCEPT", "REVISE", "REJECT", "INCONCLUSIVE"}
OUTCOMES = {"PASS", "REVISE", "FAIL", "INCONCLUSIVE"}
REVIEWER_KINDS = {"HUMAN", "MODEL", "HYBRID"}
ACTIVATION_CLAIMS = {
    "AVAILABILITY_ONLY",
    "EXPLICIT_ACTIVATION",
    "AUTOMATIC_ACTIVATION",
}
ACTIVATION_SOURCE_KINDS = {
    "INSTALLED_FILE",
    "CONFIG",
    "EXPLICIT_INVOCATION",
    "HOST_ACTIVATION_EVENT",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
UNSAFE_RAW_PROSE_FIELDS = {
    "content",
    "evidence_text",
    "final_output",
    "messages",
    "prompt",
    "quoted_evidence",
    "raw_events",
    "raw_output",
    "raw_prompt",
    "raw_response",
    "raw_stderr",
    "raw_stdout",
    "response",
    "transcript",
}


class SemanticReviewError(ValueError):
    """Raised when a semantic-review record violates the review contract."""


def trajectory_sha256(value: Any) -> str:
    """Return the stable digest used to bind a review to a trajectory value."""

    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def message_sha256(message: str) -> str:
    """Return the digest for one exact retained message string."""

    if not isinstance(message, str):
        raise TypeError("message must be a string")
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def _require_object(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise SemanticReviewError(f"{field} must be an object")
    return value


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticReviewError(f"{field} must be a non-empty string")
    return value


def _require_exact_fields(
    value: Mapping[str, Any], required: set[str], field: str
) -> None:
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        raise SemanticReviewError(f"{field} missing fields: {', '.join(missing)}")
    if unknown:
        raise SemanticReviewError(f"{field} unknown fields: {', '.join(unknown)}")


def _reject_raw_prose_fields(value: Any, path: str = "review") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in UNSAFE_RAW_PROSE_FIELDS:
                raise SemanticReviewError(
                    f"unsafe raw prose field at {child_path}: {key}"
                )
            _reject_raw_prose_fields(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_prose_fields(child, f"{path}[{index}]")


def _message_hashes(trajectory: Mapping[str, Any]) -> set[str]:
    hashes: set[str] = set()

    def add_message_values(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"content", "message", "text"} and isinstance(child, str):
                    hashes.add(message_sha256(child))
                else:
                    add_message_values(child)
        elif isinstance(value, list):
            for child in value:
                add_message_values(child)

    turns = trajectory.get("turns")
    if not isinstance(turns, list):
        return hashes
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        for field in ("prompt", "final_output"):
            if isinstance(turn.get(field), str):
                hashes.add(message_sha256(turn[field]))
        add_message_values(turn.get("raw_events", []))
    return hashes


def _validate_evidence(
    value: Any,
    field: str,
    trajectory: Mapping[str, Any],
    message_hashes: set[str],
) -> None:
    if not isinstance(value, list) or not value:
        raise SemanticReviewError(f"{field} evidence must be a non-empty list")
    turns = trajectory.get("turns")
    if not isinstance(turns, list):
        raise SemanticReviewError("trajectory turns must be a list")
    for index, raw_reference in enumerate(value):
        reference = _require_object(raw_reference, f"{field}.evidence[{index}]")
        if set(reference) == {"message_sha256"}:
            digest = reference["message_sha256"]
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise SemanticReviewError(
                    f"{field}.evidence[{index}].message_sha256 must be lowercase SHA-256"
                )
            if digest not in message_hashes:
                raise SemanticReviewError(
                    f"{field}.evidence[{index}] message hash is not present in trajectory"
                )
            continue
        if set(reference) not in ({"turn"}, {"turn", "event"}):
            raise SemanticReviewError(
                f"{field}.evidence[{index}] must reference a turn/event or message hash"
            )
        turn_number = reference["turn"]
        if (
            not isinstance(turn_number, int)
            or isinstance(turn_number, bool)
            or turn_number < 1
            or turn_number > len(turns)
        ):
            raise SemanticReviewError(
                f"{field}.evidence[{index}] turn {turn_number!r} does not exist"
            )
        if "event" not in reference:
            continue
        event_number = reference["event"]
        turn = turns[turn_number - 1]
        events = turn.get("raw_events") if isinstance(turn, dict) else None
        if (
            not isinstance(events, list)
            or not isinstance(event_number, int)
            or isinstance(event_number, bool)
            or event_number < 1
            or event_number > len(events)
        ):
            raise SemanticReviewError(
                f"{field}.evidence[{index}] event {event_number!r} does not exist in turn {turn_number}"
            )


def _rubric_contract(rubric: Any) -> tuple[str, dict[str, Any], list[str]]:
    value = _require_object(rubric, "rubric")
    rubric_id = _require_nonempty_string(value.get("id"), "rubric.id")
    score = _require_object(value.get("score"), "rubric.score")
    for field in ("minimum", "maximum", "pass_minimum"):
        candidate = score.get(field)
        if not isinstance(candidate, int) or isinstance(candidate, bool):
            raise SemanticReviewError(f"rubric.score.{field} must be an integer")
    if not score["minimum"] < score["pass_minimum"] <= score["maximum"]:
        raise SemanticReviewError("rubric score thresholds are inconsistent")
    raw_criteria = value.get("criteria")
    if not isinstance(raw_criteria, list) or not raw_criteria:
        raise SemanticReviewError("rubric.criteria must be a non-empty list")
    criteria: list[str] = []
    for index, raw_criterion in enumerate(raw_criteria):
        criterion = _require_object(raw_criterion, f"rubric.criteria[{index}]")
        criterion_id = _require_nonempty_string(
            criterion.get("id"), f"rubric.criteria[{index}].id"
        )
        if criterion_id in criteria:
            raise SemanticReviewError(f"rubric contains duplicate criterion: {criterion_id}")
        criteria.append(criterion_id)
    return rubric_id, dict(score), criteria


def _validate_activation_evidence(
    raw_activation: Any,
    trajectory: Mapping[str, Any],
    message_hashes: set[str],
) -> None:
    activation = _require_object(raw_activation, "activation_evidence")
    _require_exact_fields(activation, {"claim", "sources"}, "activation_evidence")
    claim = activation["claim"]
    if claim not in ACTIVATION_CLAIMS:
        raise SemanticReviewError(f"activation_evidence has unknown claim: {claim!r}")
    sources = activation["sources"]
    if not isinstance(sources, list) or not sources:
        raise SemanticReviewError("activation_evidence.sources must be a non-empty list")
    kinds: set[str] = set()
    for index, raw_source in enumerate(sources):
        field = f"activation_evidence.sources[{index}]"
        source = _require_object(raw_source, field)
        kind = source.get("kind")
        if kind not in ACTIVATION_SOURCE_KINDS:
            raise SemanticReviewError(f"{field} has unknown kind: {kind!r}")
        kinds.add(kind)
        if kind in {"INSTALLED_FILE", "CONFIG"}:
            _require_exact_fields(source, {"kind", "path", "sha256"}, field)
            _require_nonempty_string(source["path"], f"{field}.path")
            if not isinstance(source["sha256"], str) or not SHA256_RE.fullmatch(
                source["sha256"]
            ):
                raise SemanticReviewError(f"{field}.sha256 must be lowercase SHA-256")
        else:
            _require_exact_fields(source, {"kind", "evidence"}, field)
            _validate_evidence(source["evidence"], field, trajectory, message_hashes)
    if claim == "EXPLICIT_ACTIVATION" and not kinds.intersection(
        {"EXPLICIT_INVOCATION", "HOST_ACTIVATION_EVENT"}
    ):
        raise SemanticReviewError(
            "explicit activation requires EXPLICIT_INVOCATION or HOST_ACTIVATION_EVENT evidence"
        )
    if claim == "AUTOMATIC_ACTIVATION" and "HOST_ACTIVATION_EVENT" not in kinds:
        raise SemanticReviewError(
            "automatic activation requires HOST_ACTIVATION_EVENT evidence; installation/config only proves availability"
        )


def _validate_verdict(verdict: str, outcomes: list[str]) -> None:
    if verdict == "ACCEPT" and any(outcome != "PASS" for outcome in outcomes):
        raise SemanticReviewError("ACCEPT requires every criterion to PASS")
    if verdict == "REVISE" and (
        "REVISE" not in outcomes
        or any(outcome in {"FAIL", "INCONCLUSIVE"} for outcome in outcomes)
    ):
        raise SemanticReviewError(
            "REVISE requires a REVISE criterion and no FAIL or INCONCLUSIVE criterion"
        )
    if verdict == "REJECT" and "FAIL" not in outcomes:
        raise SemanticReviewError("REJECT requires at least one FAIL criterion")
    if verdict == "INCONCLUSIVE" and "INCONCLUSIVE" not in outcomes:
        raise SemanticReviewError(
            "INCONCLUSIVE requires at least one INCONCLUSIVE criterion"
        )


def validate_semantic_review(
    review: Any, trajectory: Any, rubric: Any
) -> None:
    """Validate one semantic review against its trajectory and rubric.

    All references are one-based.  Successful return is the only success value;
    violations raise :class:`SemanticReviewError` with a field-specific reason.
    """

    value = _require_object(review, "review")
    trajectory_value = _require_object(trajectory, "trajectory")
    _reject_raw_prose_fields(value)
    required = {
        "schema_version",
        "run_id",
        "trajectory_sha256",
        "rubric_id",
        "reviewer",
        "verdict",
        "criteria",
        "activation_evidence",
        "rationale",
        "confidence",
        "timestamp",
    }
    _require_exact_fields(value, required, "review")
    if (
        not isinstance(value["schema_version"], int)
        or isinstance(value["schema_version"], bool)
        or value["schema_version"] != SCHEMA_VERSION
    ):
        raise SemanticReviewError(f"schema_version must be {SCHEMA_VERSION}")
    if trajectory_value.get("record_type") != "teamwork_live_trajectory":
        raise SemanticReviewError(
            "trajectory record_type must be teamwork_live_trajectory"
        )
    if not isinstance(trajectory_value.get("turns"), list) or not trajectory_value[
        "turns"
    ]:
        raise SemanticReviewError("trajectory turns must be a non-empty list")
    run_id = _require_nonempty_string(value["run_id"], "run_id")
    if run_id != trajectory_value.get("run_id"):
        raise SemanticReviewError("run_id does not match trajectory")
    expected_digest = trajectory_sha256(trajectory_value)
    if value["trajectory_sha256"] != expected_digest:
        raise SemanticReviewError("trajectory_sha256 does not match trajectory")

    rubric_id, score_contract, rubric_criteria = _rubric_contract(rubric)
    if value["rubric_id"] != rubric_id:
        raise SemanticReviewError("rubric_id does not match rubric")

    reviewer = _require_object(value["reviewer"], "reviewer")
    _require_exact_fields(reviewer, {"kind", "identity", "version"}, "reviewer")
    if reviewer["kind"] not in REVIEWER_KINDS:
        raise SemanticReviewError(f"reviewer has unknown kind: {reviewer['kind']!r}")
    _require_nonempty_string(reviewer["identity"], "reviewer.identity")
    _require_nonempty_string(reviewer["version"], "reviewer.version")

    verdict = value["verdict"]
    if verdict not in VERDICTS:
        raise SemanticReviewError(f"unknown verdict: {verdict!r}")
    raw_results = value["criteria"]
    if not isinstance(raw_results, list) or not raw_results:
        raise SemanticReviewError("criteria must be a non-empty list")
    message_hashes = _message_hashes(trajectory_value)
    seen: set[str] = set()
    outcomes: list[str] = []
    for index, raw_result in enumerate(raw_results):
        field = f"criteria[{index}]"
        result = _require_object(raw_result, field)
        _require_exact_fields(
            result, {"criterion_id", "outcome", "score", "evidence"}, field
        )
        criterion_id = _require_nonempty_string(
            result["criterion_id"], f"{field}.criterion_id"
        )
        if criterion_id not in rubric_criteria:
            raise SemanticReviewError(f"unknown criteria: {criterion_id}")
        if criterion_id in seen:
            raise SemanticReviewError(f"duplicate criterion result: {criterion_id}")
        seen.add(criterion_id)
        outcome = result["outcome"]
        if outcome not in OUTCOMES:
            raise SemanticReviewError(f"{field} has unknown outcome: {outcome!r}")
        score = result["score"]
        minimum = score_contract["minimum"]
        maximum = score_contract["maximum"]
        pass_minimum = score_contract["pass_minimum"]
        if (
            not isinstance(score, int)
            or isinstance(score, bool)
            or score < minimum
            or score > maximum
        ):
            raise SemanticReviewError(
                f"{field}.score must be between {minimum} and {maximum}"
            )
        if outcome == "PASS" and score < pass_minimum:
            raise SemanticReviewError(f"{field} PASS score is below pass_minimum")
        if outcome == "REVISE" and not minimum < score < pass_minimum:
            raise SemanticReviewError(
                f"{field} REVISE score must be above minimum and below pass_minimum"
            )
        if outcome == "FAIL" and score != minimum:
            raise SemanticReviewError(f"{field} FAIL score must equal minimum")
        _validate_evidence(result["evidence"], field, trajectory_value, message_hashes)
        outcomes.append(outcome)
    missing_criteria = [item for item in rubric_criteria if item not in seen]
    if missing_criteria:
        raise SemanticReviewError(f"missing criteria: {', '.join(missing_criteria)}")
    _validate_verdict(verdict, outcomes)
    _validate_activation_evidence(
        value["activation_evidence"], trajectory_value, message_hashes
    )

    _require_nonempty_string(value["rationale"], "rationale")
    confidence = value["confidence"]
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        raise SemanticReviewError("confidence must be a number between 0 and 1")
    if not 0 <= confidence <= 1:
        raise SemanticReviewError("confidence must be a number between 0 and 1")
    timestamp = value["timestamp"]
    if not isinstance(timestamp, str) or not UTC_TIMESTAMP_RE.fullmatch(timestamp):
        raise SemanticReviewError("timestamp must be an RFC 3339 UTC timestamp")
    try:
        datetime.fromisoformat(timestamp.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise SemanticReviewError(
            "timestamp must be an RFC 3339 UTC timestamp"
        ) from exc
