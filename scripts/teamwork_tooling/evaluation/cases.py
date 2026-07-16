"""Eval case, result fixture, rubric, and ledger validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from grill_contract import has_legacy_grill_ceremony, question_count

from .contracts import *  # noqa: F403
from .sources import normalize_semantic_text, validate_semantic_sources


INTERNAL_RESEARCH_DETAIL_RE = re.compile(
    r"(?i)\b(?:teamwork|workflow stage|evidence confidence ladder|version\s*\d|"
    r"c8\s*(?:channel|label|lane)?|internal label)\b"
)
GENERIC_CAVEAT_RE = re.compile(
    r"(?i)(?:not\s+proven|cannot\s+(?:prove|confirm|establish)|"
    r"can't\s+(?:prove|confirm|establish)|does(?:n't|\s+not)\s+(?:prove|establish)|"
    r"尚未证明|尚不能证明|不能证明|无法证明|未能证明|尚未证实|不能证实|不能据此证明|"
    r"不能据此(?:确认|认定)|无法(?:确认|认定)|不能确认|不能断定)"
)
HYPOTHETICAL_CAUSE_SIGNALS = (
    re.compile(r"(?i)\bnatural change\b|自然变化"),
    re.compile(r"(?i)\btime(?: changes?)?\b|时间变化"),
    re.compile(r"(?i)\benvironment\b|环境"),
    re.compile(r"(?i)\bother (?:support|help)\b|其他(?:支持|帮助)"),
    re.compile(r"(?i)\bparticipant differences?\b|参与者差异"),
    re.compile(r"(?i)\bsubjective expectations?\b|主观期待"),
)
EXTRA_COMMUNITY_ACTION_RE = re.compile(
    r"(?i)\b(?:expand|increase) the sample\b|\bcollect more feedback\b|"
    r"扩大样本|增加样本|收集更多反馈|继续跟踪"
)
ATTRIBUTION_BOUNDARY_RE = re.compile(
    r"(?i)(?:cannot|can't) tell how much[^.;。；]*came from|"
    r"(?:无法|不能)(?:判断|确定)[^。；;]*有多少[^。；;]*来自"
)
IRRELEVANT_PROCESS_NARRATION_RE = re.compile(
    r"(?i)(?:"
    r"\b(?:i|we)\s+(?:(?:first|then)\s+)?(?:inspected|analyzed|validated|used|loaded|"
    r"opened|routed|dispatched|ran|recovered)\b|"
    r"\brouted\s+(?:this|the\s+(?:result|request|answer))\s+through\b|"
    r"\bthe\s+workflow\s+(?:routed|validated|classified|recorded)\b"
    r")"
)
FORCED_CAUSE_RE = re.compile(
    r"(?i)\b(?:because|so that|in order to|it matters because)\b|"
    r"\bwhich\s+(?:helps|ensures|prevents)\b"
)
FORCED_ACTION_RE = re.compile(
    r"(?i)(?:"
    r"\b(?:you should|please)\s+(?:run|execute)\b|"
    r"\bnext[, :]\s*(?:run|execute)\b|"
    r"(?:^|[;:,.!?]\s*)run\s+(?:it|this|the command)\b|"
    r"\b(?:run|execute)\s+(?:it|this)\s+now\b"
    r")"
)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise EvalError(f"{display_path(path)}: invalid JSON: {exc}") from exc


def require_string(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{display_path(path)}: {field} must be a non-empty string")
    return value


def require_string_list(value: Any, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise EvalError(f"{display_path(path)}: {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise EvalError(f"{display_path(path)}: {field} must contain non-empty strings")
    return value


def validate_discussion_handoff_case(data: dict[str, Any], path: Path) -> None:
    answered = require_string_list(
        data.get("answered_decisions"), "answered_decisions", path
    )
    if len(answered) < 2:
        raise EvalError(
            f"{display_path(path)}: handoff trajectory must preserve at least two answered decisions"
        )
    expected_next = require_string(
        data.get("expected_next_decision"), "expected_next_decision", path
    )
    trajectory = data.get("trajectory")
    if not isinstance(trajectory, list) or not trajectory:
        raise EvalError(
            f"{display_path(path)}: handoff trajectory must be a non-empty authored turn list"
        )

    assistant_turns: list[str] = []
    for index, turn in enumerate(trajectory, start=1):
        if not isinstance(turn, dict) or set(turn) != {"user", "assistant"}:
            raise EvalError(
                f"{display_path(path)}: handoff trajectory turn {index} must contain exactly user and assistant"
            )
        require_string(turn.get("user"), "trajectory.user", path)
        assistant_turns.append(
            require_string(turn.get("assistant"), "trajectory.assistant", path)
        )

    authored_output = "\n".join(assistant_turns)
    normalized_output = normalize_semantic_text(authored_output)
    for decision in answered:
        if normalize_semantic_text(decision) not in normalized_output:
            raise EvalError(
                f"{display_path(path)}: handoff trajectory loses answered decision: {decision}"
            )

    questions = [
        line.strip()
        for line in authored_output.splitlines()
        if "?" in line or "？" in line
    ]
    if question_count(authored_output) != 1 or len(questions) != 1:
        raise EvalError(
            f"{display_path(path)}: handoff trajectory must ask exactly one next decision"
        )
    normalized_question = normalize_semantic_text(questions[0])
    repeated = [
        decision
        for decision in answered
        if normalize_semantic_text(decision) in normalized_question
    ]
    if repeated:
        raise EvalError(
            f"{display_path(path)}: handoff trajectory repeats answered decision: {repeated[0]}"
        )
    if normalize_semantic_text(expected_next) not in normalized_question:
        raise EvalError(
            f"{display_path(path)}: handoff trajectory does not ask expected next decision"
        )


def validate_discussion_recovery_case(data: dict[str, Any], path: Path) -> None:
    artifact = require_string(data.get("authored_artifact"), "authored_artifact", path)
    if not re.search(r"(?m)^# (?!Discussion\s*$|<)[^\n]+$", artifact):
        raise EvalError(
            f"{display_path(path)}: recovery artifact must have a specific topic H1"
        )

    anchors = data.get("recovery_anchors")
    required = {"goal", "settled", "still_open", "key_evidence", "continue_here"}
    if not isinstance(anchors, dict) or set(anchors) != required:
        raise EvalError(
            f"{display_path(path)}: recovery_anchors must contain exactly the five recovery sections"
        )
    headings = {
        "goal": "Goal",
        "settled": "Settled",
        "still_open": "Still open",
        "key_evidence": "Key evidence",
        "continue_here": "Continue here",
    }
    for key in sorted(required):
        anchor = require_string(anchors.get(key), f"recovery_anchors.{key}", path)
        heading = headings[key]
        match = re.search(
            rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", artifact
        )
        if not match:
            raise EvalError(
                f"{display_path(path)}: recovery artifact missing {heading} section"
            )
        if normalize_semantic_text(anchor) not in normalize_semantic_text(match.group(1)):
            raise EvalError(
                f"{display_path(path)}: {heading} loses its human recovery anchor"
            )

    retired = ("Route Map", "Textual Playback", "Update Rules", "Decision State")
    if any(re.search(rf"(?m)^## {re.escape(heading)}\s*$", artifact) for heading in retired):
        raise EvalError(
            f"{display_path(path)}: recovery artifact retains a retired required section"
        )


def validate_audience_reply_case(data: dict[str, Any], path: Path) -> None:
    """Keep the authored community-research contrast useful as an offline oracle.

    The checks intentionally validate a compact, authored positive response and
    explicit negative controls. They do not claim to score arbitrary model prose
    or establish live model behavior.
    """

    response = require_string(data.get("authored_response"), "authored_response", path)
    checks = data.get("response_checks")
    required_checks = {
        "opening_conclusion",
        "audience_meaning",
        "causal_explanation",
        "material_uncertainty",
        "uncertainty_impact",
        "next_step",
    }
    if not isinstance(checks, dict) or set(checks) != required_checks:
        raise EvalError(
            f"{display_path(path)}: response_checks must contain exactly "
            f"{sorted(required_checks)}"
        )
    normalized_response = normalize_semantic_text(response)
    for field in sorted(required_checks):
        phrase = require_string(checks[field], f"response_checks.{field}", path)
        if normalize_semantic_text(phrase) not in normalized_response:
            raise EvalError(
                f"{display_path(path)}: authored_response loses {field}"
            )

    first_sentence = response.split(".", 1)[0]
    if IRRELEVANT_PROCESS_NARRATION_RE.search(response):
        raise EvalError(
            f"{display_path(path)}: authored_response includes irrelevant workflow narration"
        )
    if normalize_semantic_text(checks["opening_conclusion"]) not in normalize_semantic_text(
        first_sentence
    ):
        raise EvalError(
            f"{display_path(path)}: authored_response must lead with the conclusion"
        )
    if INTERNAL_RESEARCH_DETAIL_RE.search(response):
        raise EvalError(
            f"{display_path(path)}: authored_response exposes irrelevant internal detail"
        )
    if GENERIC_CAVEAT_RE.search(normalized_response):
        raise EvalError(
            f"{display_path(path)}: authored_response uses a generic proof-status caveat"
        )
    cause_signals = sum(
        bool(pattern.search(response)) for pattern in HYPOTHETICAL_CAUSE_SIGNALS
    )
    if cause_signals >= 2:
        raise EvalError(
            f"{display_path(path)}: authored_response lists imagined alternative causes"
        )
    if EXTRA_COMMUNITY_ACTION_RE.search(response):
        raise EvalError(
            f"{display_path(path)}: authored_response adds a second independent next action"
        )
    if len(ATTRIBUTION_BOUNDARY_RE.findall(response)) > 1:
        raise EvalError(
            f"{display_path(path)}: authored_response repeats the attribution boundary"
        )

    controls = data.get("negative_controls")
    if not isinstance(controls, list) or len(controls) != 4:
        raise EvalError(
            f"{display_path(path)}: negative_controls must contain four named failure modes"
        )
    expected_controls = {
        "workflow_narration",
        "irrelevant_internal_detail",
        "generic_caveat_repetition",
        "false_certainty",
    }
    seen_controls: set[str] = set()
    for index, control in enumerate(controls, start=1):
        if not isinstance(control, dict) or set(control) != {"id", "response"}:
            raise EvalError(
                f"{display_path(path)}: negative control {index} must contain exactly id and response"
            )
        control_id = require_string(control.get("id"), "negative_controls.id", path)
        text = require_string(control.get("response"), "negative_controls.response", path)
        if control_id in seen_controls:
            raise EvalError(f"{display_path(path)}: duplicate negative control: {control_id}")
        seen_controls.add(control_id)
        normalized = normalize_semantic_text(text)
        if control_id == "workflow_narration" and not IRRELEVANT_PROCESS_NARRATION_RE.search(text):
            raise EvalError(
                f"{display_path(path)}: workflow_narration control no longer demonstrates workflow leakage"
            )
        if control_id == "irrelevant_internal_detail":
            has_version = bool(re.search(r"\bversion\s*\d", normalized))
            has_self_invented_label = bool(
                re.search(
                    r"\b(?:c8\s*(?:channel|label|lane)?|evidence confidence ladder|internal label)\b",
                    normalized,
                )
            )
            if not has_version or not has_self_invented_label:
                raise EvalError(
                    f"{display_path(path)}: irrelevant_internal_detail control must combine a version with a self-invented label"
                )
        if control_id == "generic_caveat_repetition" and len(GENERIC_CAVEAT_RE.findall(normalized)) < 2:
            raise EvalError(
                f"{display_path(path)}: generic_caveat_repetition control must repeat a generic caveat in English or Chinese"
            )
        if control_id == "false_certainty" and not re.search(
            r"\b(?:the program worked|proves the program worked|definitely caused)\b",
            normalized,
        ):
            raise EvalError(
                f"{display_path(path)}: false_certainty control no longer demonstrates overclaiming"
            )
    if seen_controls != expected_controls:
        raise EvalError(
            f"{display_path(path)}: negative_controls must cover "
            f"{', '.join(sorted(expected_controls))}"
        )


def validate_reader_argument_case(data: dict[str, Any], path: Path) -> None:
    """Keep the reader-facing argument as a compact authored contrast.

    This fixture checks its own anchors and negative controls. It does not claim
    that an arbitrary live model will follow the argument order.
    """

    response = require_string(data.get("authored_response"), "authored_response", path)
    checks = data.get("response_checks")
    required_checks = {
        "conclusion",
        "observed_basis",
        "interpretation",
        "current_decision",
        "next_discriminator",
    }
    if not isinstance(checks, dict) or set(checks) != required_checks:
        raise EvalError(
            f"{display_path(path)}: reader argument response_checks must contain exactly "
            f"{sorted(required_checks)}"
        )

    normalized_response = normalize_semantic_text(response)
    positions: list[int] = []
    for field in (
        "conclusion",
        "observed_basis",
        "interpretation",
        "current_decision",
        "next_discriminator",
    ):
        phrase = require_string(checks[field], f"response_checks.{field}", path)
        position = normalized_response.find(normalize_semantic_text(phrase))
        if position < 0:
            raise EvalError(f"{display_path(path)}: authored_response loses {field}")
        positions.append(position)
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise EvalError(
            f"{display_path(path)}: reader argument must keep conclusion, basis, "
            "interpretation, decision, and discriminator in order"
        )
    if GENERIC_CAVEAT_RE.search(response):
        raise EvalError(
            f"{display_path(path)}: reader argument uses a stock proof-status caveat"
        )
    if IRRELEVANT_PROCESS_NARRATION_RE.search(response):
        raise EvalError(
            f"{display_path(path)}: reader argument includes irrelevant process narration"
        )
    if re.search(r"(?i)\bq9\b|证据阶梯|自创标签", response):
        raise EvalError(
            f"{display_path(path)}: reader argument introduces a self-invented label"
        )
    if re.search(r"C8\s*(?:表示|指(?:的是)?|means?)\s*(?:八|eight)|八个通道", response):
        raise EvalError(
            f"{display_path(path)}: reader argument infers meaning from the C8 identifier"
        )

    controls = data.get("negative_controls")
    expected_controls = {
        "fact_dump",
        "generic_proof_status",
        "invented_label",
        "identifier_as_evidence",
        "mainline_displaced",
    }
    if not isinstance(controls, list) or len(controls) != len(expected_controls):
        raise EvalError(
            f"{display_path(path)}: reader argument negative_controls must contain "
            "five named failure modes"
        )
    seen_controls: set[str] = set()
    for index, control in enumerate(controls, start=1):
        if not isinstance(control, dict) or set(control) != {"id", "response"}:
            raise EvalError(
                f"{display_path(path)}: reader argument negative control {index} "
                "must contain exactly id and response"
            )
        control_id = require_string(control.get("id"), "negative_controls.id", path)
        text = require_string(control.get("response"), "negative_controls.response", path)
        if control_id in seen_controls:
            raise EvalError(
                f"{display_path(path)}: duplicate reader argument negative control: {control_id}"
            )
        seen_controls.add(control_id)
        normalized = normalize_semantic_text(text)
        if control_id == "fact_dump" and (
            normalize_semantic_text(checks["interpretation"]) in normalized
            or normalize_semantic_text(checks["next_discriminator"]) in normalized
        ):
            raise EvalError(
                f"{display_path(path)}: fact_dump control no longer omits the explanation or discriminator"
            )
        if control_id == "generic_proof_status" and not GENERIC_CAVEAT_RE.search(text):
            raise EvalError(
                f"{display_path(path)}: generic_proof_status control loses its stock caveat"
            )
        if control_id == "invented_label" and not re.search(
            r"(?i)\bq9\b|证据阶梯|自创标签", text
        ):
            raise EvalError(
                f"{display_path(path)}: invented_label control loses its invented term"
            )
        if control_id == "identifier_as_evidence" and not re.search(
            r"C8\s*(?:表示|指(?:的是)?|means?)\s*(?:八|eight)|八个通道", text
        ):
            raise EvalError(
                f"{display_path(path)}: identifier_as_evidence control loses its unsupported inference"
            )
        if control_id == "mainline_displaced" and not re.search(
            r"讨论文档|持久化|版本|工作流", text
        ):
            raise EvalError(
                f"{display_path(path)}: mainline_displaced control loses its status diversion"
            )
    if seen_controls != expected_controls:
        raise EvalError(
            f"{display_path(path)}: reader argument negative_controls must cover "
            f"{', '.join(sorted(expected_controls))}"
        )


def validate_continuing_mainline_case(data: dict[str, Any], path: Path) -> None:
    """Protect the authored contrast between an advancing discussion and status drift."""

    mainline = require_string(data.get("mainline"), "mainline", path)
    turns = data.get("turns")
    anchors = data.get("turn_anchors")
    if not isinstance(turns, list) or len(turns) != 2:
        raise EvalError(
            f"{display_path(path)}: continuing discussion must contain exactly two authored turns"
        )
    if not isinstance(anchors, list) or len(anchors) != len(turns):
        raise EvalError(
            f"{display_path(path)}: continuing discussion must contain anchors for each turn"
        )

    for index, (turn, turn_anchors) in enumerate(zip(turns, anchors), start=1):
        if not isinstance(turn, dict) or set(turn) != {"user", "assistant"}:
            raise EvalError(
                f"{display_path(path)}: continuing discussion turn {index} must contain exactly user and assistant"
            )
        require_string(turn.get("user"), "turns.user", path)
        assistant = require_string(turn.get("assistant"), "turns.assistant", path)
        if not isinstance(turn_anchors, dict) or set(turn_anchors) != {
            "answer",
            "mainline",
            "advance",
        }:
            raise EvalError(
                f"{display_path(path)}: continuing discussion turn {index} anchors must contain "
                "answer, mainline, and advance"
            )
        normalized = normalize_semantic_text(assistant)
        for field in ("answer", "mainline", "advance"):
            phrase = require_string(turn_anchors.get(field), f"turn_anchors.{field}", path)
            if normalize_semantic_text(phrase) not in normalized:
                raise EvalError(
                    f"{display_path(path)}: continuing discussion turn {index} loses {field}"
                )
        first_sentence = re.split(r"[。.!?！？]", assistant, maxsplit=1)[0]
        if normalize_semantic_text(turn_anchors["answer"]) not in normalize_semantic_text(
            first_sentence
        ):
            raise EvalError(
                f"{display_path(path)}: continuing discussion turn {index} must answer before status"
            )
        if normalize_semantic_text(mainline) not in normalized:
            raise EvalError(
                f"{display_path(path)}: continuing discussion turn {index} loses the mainline"
            )
        if re.search(r"版本|讨论文档|持久化|工作流|三个文件", assistant):
            raise EvalError(
                f"{display_path(path)}: continuing discussion turn {index} includes status drift"
            )

    controls = data.get("negative_controls")
    expected_controls = {"status_displacement", "topic_switch", "invented_label"}
    if not isinstance(controls, list) or len(controls) != len(expected_controls):
        raise EvalError(
            f"{display_path(path)}: continuing discussion negative_controls must contain "
            "three named failure modes"
        )
    seen_controls: set[str] = set()
    for index, control in enumerate(controls, start=1):
        if not isinstance(control, dict) or set(control) != {"id", "response"}:
            raise EvalError(
                f"{display_path(path)}: continuing discussion negative control {index} "
                "must contain exactly id and response"
            )
        control_id = require_string(control.get("id"), "negative_controls.id", path)
        text = require_string(control.get("response"), "negative_controls.response", path)
        if control_id in seen_controls:
            raise EvalError(
                f"{display_path(path)}: duplicate continuing discussion negative control: {control_id}"
            )
        seen_controls.add(control_id)
        if control_id == "status_displacement" and not re.search(
            r"版本|讨论文档|持久化|工作流", text
        ):
            raise EvalError(
                f"{display_path(path)}: status_displacement control loses the status diversion"
            )
        if control_id == "topic_switch" and normalize_semantic_text(mainline) in normalize_semantic_text(text):
            raise EvalError(
                f"{display_path(path)}: topic_switch control still follows the mainline"
            )
        if control_id == "invented_label" and not re.search(
            r"(?i)\bq9\b|证据阶梯|自创标签", text
        ):
            raise EvalError(
                f"{display_path(path)}: invented_label control loses its invented term"
            )
    if seen_controls != expected_controls:
        raise EvalError(
            f"{display_path(path)}: continuing discussion negative_controls must cover "
            f"{', '.join(sorted(expected_controls))}"
        )


def validate_skill_explanation_contrast_case(data: dict[str, Any], path: Path) -> None:
    """Keep skill relevance distinct from engineering-process leakage."""

    response = require_string(data.get("authored_response"), "authored_response", path)
    normalized_response = normalize_semantic_text(response)
    for anchor in ("teamwork-review", "read-only", "authorization"):
        if normalize_semantic_text(anchor) not in normalized_response:
            raise EvalError(
                f"{display_path(path)}: useful skill explanation loses {anchor}"
            )
    if (
        "skills/" in response.casefold()
        or "subagent" in normalized_response
        or re.search(r"\b\d+\s+tests?\b", normalized_response)
    ):
        raise EvalError(
            f"{display_path(path)}: useful skill explanation includes engineering process inventory"
        )
    if IRRELEVANT_PROCESS_NARRATION_RE.search(response):
        raise EvalError(
            f"{display_path(path)}: useful skill explanation includes irrelevant route or workflow narration"
        )
    if "\n" in response or len(response) > 180:
        raise EvalError(
            f"{display_path(path)}: useful skill explanation must stay brief"
        )

    control = data.get("negative_control")
    if not isinstance(control, dict) or set(control) != {"id", "response"}:
        raise EvalError(
            f"{display_path(path)}: negative_control must contain exactly id and response"
        )
    if control.get("id") != "engineering_process_dump":
        raise EvalError(
            f"{display_path(path)}: negative_control must be engineering_process_dump"
        )
    dumped = normalize_semantic_text(
        require_string(control.get("response"), "negative_control.response", path)
    )
    required_dump_signals = ("skills/teamwork-review/skill.md", "subagent", "42 tests")
    missing = [
        signal
        for signal in required_dump_signals
        if normalize_semantic_text(signal) not in dumped
    ]
    if missing:
        raise EvalError(
            f"{display_path(path)}: engineering process dump loses: {', '.join(missing)}"
        )
    if not IRRELEVANT_PROCESS_NARRATION_RE.search(control["response"]):
        raise EvalError(
            f"{display_path(path)}: engineering process dump loses irrelevant route or workflow narration"
        )


def validate_one_sentence_fact_control(data: dict[str, Any], path: Path) -> None:
    """Protect a simple fact from mandatory explanation or action padding."""

    response = require_string(data.get("authored_response"), "authored_response", path)
    fact = require_string(data.get("fact_anchor"), "fact_anchor", path)
    if normalize_semantic_text(fact) not in normalize_semantic_text(response):
        raise EvalError(f"{display_path(path)}: one-sentence control loses the fact")
    if "\n" in response or len(re.findall(r"[.!?。！？](?:\s|$)", response)) != 1:
        raise EvalError(
            f"{display_path(path)}: simple fact must remain one sentence"
        )
    if len(response.split()) > 12:
        raise EvalError(
            f"{display_path(path)}: simple fact exceeds the shortest complete answer"
        )
    if FORCED_CAUSE_RE.search(response):
        raise EvalError(
            f"{display_path(path)}: simple fact adds a forced causal explanation"
        )
    if FORCED_ACTION_RE.search(response):
        raise EvalError(f"{display_path(path)}: simple fact adds a forced action")

    controls = data.get("negative_controls")
    if not isinstance(controls, list) or len(controls) != 2:
        raise EvalError(
            f"{display_path(path)}: one-sentence control must contain forced-cause and forced-action controls"
        )
    expected_controls = {"forced_cause", "forced_action"}
    seen_controls: set[str] = set()
    for index, control in enumerate(controls, start=1):
        if not isinstance(control, dict) or set(control) != {"id", "response"}:
            raise EvalError(
                f"{display_path(path)}: fact negative control {index} must contain exactly id and response"
            )
        control_id = require_string(control.get("id"), "negative_controls.id", path)
        text = require_string(control.get("response"), "negative_controls.response", path)
        if control_id in seen_controls:
            raise EvalError(f"{display_path(path)}: duplicate fact negative control: {control_id}")
        seen_controls.add(control_id)
        if control_id == "forced_cause" and not FORCED_CAUSE_RE.search(text):
            raise EvalError(
                f"{display_path(path)}: forced_cause control loses its causal padding"
            )
        if control_id == "forced_action" and not FORCED_ACTION_RE.search(text):
            raise EvalError(
                f"{display_path(path)}: forced_action control loses its action padding"
            )
    if seen_controls != expected_controls:
        raise EvalError(
            f"{display_path(path)}: fact negative controls must cover "
            f"{', '.join(sorted(expected_controls))}"
        )


def _question_texts(text: str) -> list[str]:
    """Return authored question fragments without claiming semantic parsing."""

    return [fragment.strip() for fragment in re.findall(r"[^.?!？\n]*[?？]", text)]


def validate_mainline_distraction_case(data: dict[str, Any], path: Path) -> None:
    """Validate authored anchors for a mainline-versus-detail contrast.

    This protects the fixture itself. The matching output sample remains an
    authored static contract, not evidence that an arbitrary model will retain
    the mainline in a live conversation.
    """

    mainline_anchor = require_string(data.get("mainline_anchor"), "mainline_anchor", path)
    question_anchor = require_string(data.get("question_anchor"), "question_anchor", path)
    distractions = require_string_list(
        data.get("implementation_distractions"), "implementation_distractions", path
    )
    if len(distractions) < 2:
        raise EvalError(
            f"{display_path(path)}: mainline distraction fixture needs at least two implementation details"
        )
    if normalize_semantic_text(mainline_anchor) == normalize_semantic_text(question_anchor):
        raise EvalError(
            f"{display_path(path)}: mainline and question anchors must describe different parts of the response"
        )


def validate_mainline_distraction_output(
    case: dict[str, Any], trajectory: list[dict[str, Any]], path: Path, index: int
) -> None:
    """Ensure the authored Grill trajectory asks the public decision, not a detail."""

    question_turns = [
        turn
        for turn in trajectory
        if turn["asked_candidates"] == ["public_claim_scope"]
    ]
    if len(question_turns) != 1:
        raise EvalError(
            f"{display_path(path)}:{index}: mainline distraction fixture must ask exactly the public_claim_scope decision"
        )
    question_turn = question_turns[0]["assistant"]
    normalized_turn = normalize_semantic_text(question_turn)
    for field in ("mainline_anchor", "question_anchor"):
        anchor = normalize_semantic_text(case[field])
        if anchor not in normalized_turn:
            raise EvalError(
                f"{display_path(path)}:{index}: mainline distraction fixture does not preserve {field}"
            )

    question_texts = _question_texts(question_turn)
    if len(question_texts) != 1:
        raise EvalError(
            f"{display_path(path)}:{index}: mainline distraction fixture must contain one public-decision question"
        )
    normalized_question = normalize_semantic_text(question_texts[0])
    for detail in case["implementation_distractions"]:
        if normalize_semantic_text(detail) in normalized_question:
            raise EvalError(
                f"{display_path(path)}:{index}: implementation detail displaced the public-decision question: {detail}"
            )

    authored_reply = "\n".join(turn["assistant"] for turn in trajectory)
    normalized_reply = normalize_semantic_text(authored_reply)
    exposed = [
        detail
        for detail in case["implementation_distractions"]
        if normalize_semantic_text(detail) in normalized_reply
    ]
    if exposed:
        raise EvalError(
            f"{display_path(path)}:{index}: ordinary reply exposes irrelevant implementation detail: "
            + ", ".join(exposed)
        )


def normalize_contract_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def is_package_relative(value: str) -> bool:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    try:
        (ROOT / candidate).resolve().relative_to(ROOT)
    except ValueError:
        return False
    return True


def is_glob_like(value: str) -> bool:
    return any(char in value for char in GLOB_CHARS)


def require_evidence_path(value: Any, field: str, path: Path, index: int) -> str:
    item = require_string(value, field, path)
    if item == PLACEHOLDER:
        raise EvalError(f"{display_path(path)}:{index}: {field} must not be {PLACEHOLDER}")
    if not is_package_relative(item):
        raise EvalError(f"{display_path(path)}:{index}: {field} must be package-relative: {item}")
    item_path = ROOT / item
    if not item_path.exists():
        raise EvalError(f"{display_path(path)}:{index}: {field} path does not exist: {item}")
    return item


def validate_owned_files(items: list[str], path: Path, index: int) -> None:
    for item in items:
        if item == PLACEHOLDER:
            raise EvalError(f"{display_path(path)}:{index}: owned_files must not contain {PLACEHOLDER}")
        if not is_package_relative(item):
            raise EvalError(f"{display_path(path)}:{index}: owned_files entry must be package-relative: {item}")
        if is_glob_like(item):
            continue
        if not (ROOT / item).exists():
            raise EvalError(f"{display_path(path)}:{index}: owned_files path does not exist: {item}")


def validate_target(target: str, path: Path) -> None:
    if target.startswith("/") or ".." in Path(target).parts:
        raise EvalError(f"{display_path(path)}: target must be package-relative: {target}")
    if not target.startswith(TARGET_PREFIXES):
        raise EvalError(f"{display_path(path)}: target is not an allowed package surface: {target}")
    target_path = (ROOT / target).resolve()
    try:
        target_path.relative_to(ROOT)
    except ValueError as exc:
        raise EvalError(f"{display_path(path)}: target points outside repo: {target}") from exc
    if not target_path.is_file():
        raise EvalError(f"{display_path(path)}: target does not exist: {target}")



def validate_case(path: Path, known_rubrics: set[str]) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise EvalError(f"{display_path(path)}: case must be a JSON object")
    missing = sorted(REQUIRED_CASE_FIELDS - set(data))
    if missing:
        raise EvalError(f"{display_path(path)}: missing required fields: {', '.join(missing)}")

    case_id = require_string(data["id"], "id", path)
    if not ID_RE.match(case_id):
        raise EvalError(f"{display_path(path)}: id must be kebab-case")

    split = require_string(data["split"], "split", path)
    if split not in SPLITS:
        raise EvalError(f"{display_path(path)}: split must be one of {sorted(SPLITS)}")

    source = require_string(data["source"], "source", path)
    if source not in SOURCES:
        raise EvalError(f"{display_path(path)}: source must be one of {sorted(SOURCES)}")

    target = require_string(data["target"], "target", path)
    validate_target(target, path)

    platforms = require_string_list(data["platforms"], "platforms", path)
    unknown_platforms = sorted(set(platforms) - PLATFORMS)
    if unknown_platforms:
        raise EvalError(f"{display_path(path)}: unknown platforms: {', '.join(unknown_platforms)}")

    require_string(data["prompt"], "prompt", path)
    if not isinstance(data["expected"], dict) or not data["expected"]:
        raise EvalError(f"{display_path(path)}: expected must be a non-empty object")
    if case_id in REQUIRED_CASE_TARGET_ROUTES:
        required_target, required_route = REQUIRED_CASE_TARGET_ROUTES[case_id]
        if target != required_target:
            raise EvalError(
                f"{display_path(path)}: {case_id} target must be {required_target}"
            )
        if data["expected"].get("route") != required_route:
            raise EvalError(
                f"{display_path(path)}: {case_id} route must be {required_route}"
            )
    if case_id in REQUIRED_ACTIVATION_CASES:
        language, route, required_target, observable = REQUIRED_ACTIVATION_CASES[case_id]
        expected = data["expected"]
        if target != required_target:
            raise EvalError(
                f"{display_path(path)}: weak-cue target must be {required_target}"
            )
        for field, required in (
            ("language", language),
            ("route", route),
            ("observable", observable),
        ):
            if expected.get(field) != required:
                raise EvalError(
                    f"{display_path(path)}: weak-cue {field} must be {required}"
                )
        requires = expected.get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: weak-cue expected.requires must be a string list"
            )
        missing_activation = sorted(REQUIRED_ACTIVATION_COVERAGE - set(requires))
        if missing_activation:
            raise EvalError(
                f"{display_path(path)}: weak-cue coverage missing: "
                f"{', '.join(missing_activation)}"
            )
        prompt = data["prompt"]
        if ACTIVATION_PROMPT_STAGE_RE.search(prompt):
            raise EvalError(
                f"{display_path(path)}: weak-cue prompt must omit stage and skill names"
            )
        if set(platforms) != PLATFORMS:
            raise EvalError(
                f"{display_path(path)}: weak-cue case must cover codex, cursor, and claude"
            )
    require_string_list(data["must"], "must", path)
    require_string_list(data["must_not"], "must_not", path)
    evidence = data["evidence"]
    if not (
        isinstance(evidence, str)
        and evidence.strip()
        or isinstance(evidence, list)
        and evidence
        and all(isinstance(item, str) and item.strip() for item in evidence)
    ):
        raise EvalError(f"{display_path(path)}: evidence must be a non-empty string or string list")
    if case_id in REQUIRED_ACTIVATION_CASES:
        evidence_text = " ".join(evidence) if isinstance(evidence, list) else evidence
        if "does not prove live model activation" not in evidence_text.casefold():
            raise EvalError(
                f"{display_path(path)}: weak-cue evidence must retain its static-only limit"
            )

    serialized_case = json.dumps(data, sort_keys=True).lower()
    retired_case_terms = [
        term for term in RETIRED_ACTIVE_CASE_TERMS if term in serialized_case
    ]
    if retired_case_terms:
        raise EvalError(
            f"{display_path(path)}: retired workflow term remains: "
            f"{', '.join(retired_case_terms)}"
        )

    if case_id in REQUIRED_WORKING_FACTS_CASES:
        requires = data["expected"].get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: Working Facts expected.requires must be a string list"
            )
        missing_working_facts = sorted(
            REQUIRED_WORKING_FACTS_CASES[case_id] - set(requires)
        )
        if missing_working_facts:
            raise EvalError(
                f"{display_path(path)}: Working Facts coverage missing: "
                f"{', '.join(missing_working_facts)}"
            )

    if case_id in REQUIRED_MINIMALITY_CASES:
        requires = data["expected"].get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: minimality expected.requires must be a string list"
            )
        missing_minimality = sorted(
            REQUIRED_MINIMALITY_CASES[case_id] - set(requires)
        )
        if missing_minimality:
            raise EvalError(
                f"{display_path(path)}: minimality coverage missing: "
                f"{', '.join(missing_minimality)}"
            )

    if case_id in REQUIRED_SEMANTIC_INIT_CASES:
        requires = data["expected"].get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: semantic-init expected.requires must be a string list"
            )
        normalized_requires = {normalize_contract_key(item) for item in requires}
        missing_semantic_init = sorted(
            REQUIRED_SEMANTIC_INIT_CASES[case_id] - normalized_requires
        )
        if missing_semantic_init:
            raise EvalError(
                f"{display_path(path)}: semantic-init coverage missing: "
                f"{', '.join(missing_semantic_init)}"
            )

    if case_id in REQUIRED_DISCUSSION_CASES:
        requires = data["expected"].get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: discussion expected.requires must be a string list"
            )
        normalized_requires = {normalize_contract_key(item) for item in requires}
        missing_discussion = sorted(
            REQUIRED_DISCUSSION_CASES[case_id] - normalized_requires
        )
        if missing_discussion:
            raise EvalError(
                f"{display_path(path)}: discussion coverage missing: "
                f"{', '.join(missing_discussion)}"
            )
        if case_id == "discussion-handoff-recovery":
            validate_discussion_handoff_case(data, path)
        if case_id == "discussion-human-recovery":
            validate_discussion_recovery_case(data, path)
        if case_id == "discussion-resume-no-new-input":
            normalized_must = normalize_semantic_text("\n".join(data["must"]))
            normalized_must_not = normalize_semantic_text("\n".join(data["must_not"]))
            for phrase in (
                "run inspect and ask the saved unresolved question",
                "keep the resume read-only when the user provides no new decision, evidence, or continuation point",
            ):
                if normalize_semantic_text(phrase) not in normalized_must:
                    raise EvalError(
                        f"{display_path(path)}: no-input resume must preserve {phrase}"
                    )
            for phrase in (
                "run schema or apply",
                "invent new facts or refine the saved question on the user's behalf",
            ):
                if normalize_semantic_text(phrase) not in normalized_must_not:
                    raise EvalError(
                        f"{display_path(path)}: no-input resume must forbid {phrase}"
                    )

    for label, required_cases in (
        ("audience", REQUIRED_AUDIENCE_CASES),
        ("handoff", REQUIRED_HANDOFF_CASES),
        ("rule-maintenance", REQUIRED_RULE_MAINTENANCE_CASES),
    ):
        if case_id not in required_cases:
            continue
        requires = data["expected"].get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: {label} expected.requires must be a string list"
            )
        normalized_requires = {normalize_contract_key(item) for item in requires}
        missing = sorted(required_cases[case_id] - normalized_requires)
        if missing:
            raise EvalError(
                f"{display_path(path)}: {label} coverage missing: "
                f"{', '.join(missing)}"
            )
    if case_id == "audience-first-community-research":
        validate_audience_reply_case(data, path)
    if case_id == "audience-reader-argument":
        validate_reader_argument_case(data, path)
    if case_id == "audience-continuing-mainline":
        validate_continuing_mainline_case(data, path)
    if case_id == "audience-skill-explanation-contrast":
        validate_skill_explanation_contrast_case(data, path)
    if case_id == "audience-one-sentence-fact-control":
        validate_one_sentence_fact_control(data, path)
    if case_id == "grill-question-value-stop":
        validate_mainline_distraction_case(data, path)

    if case_id in SEMANTIC_QUESTION_CASES:
        retired = sorted(
            {"expected_question_ids", "blocked_route", "expected_close"} & set(data)
        )
        if retired:
            raise EvalError(
                f"{display_path(path)}: retired grill protocol fields remain: {', '.join(retired)}"
            )
        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise EvalError(f"{display_path(path)}: candidates must be a non-empty list")
        candidate_ids: set[str] = set()
        user_decision_ids: set[str] = set()
        for candidate_index, candidate in enumerate(candidates, start=1):
            if not isinstance(candidate, dict):
                raise EvalError(
                    f"{display_path(path)}: candidate {candidate_index} must be an object"
                )
            required_candidate_fields = {
                "candidate_id", "owner", "grounding_required", "expected_action"
            }
            if set(candidate) != required_candidate_fields:
                raise EvalError(
                    f"{display_path(path)}: candidate {candidate_index} must contain exactly "
                    f"{sorted(required_candidate_fields)}"
                )
            candidate_id = require_string(
                candidate.get("candidate_id"), "candidate_id", path
            )
            if not CANDIDATE_ID_RE.fullmatch(candidate_id):
                raise EvalError(
                    f"{display_path(path)}: candidate_id must be snake_case: {candidate_id}"
                )
            if candidate_id in candidate_ids:
                raise EvalError(f"{display_path(path)}: duplicate candidate_id: {candidate_id}")
            candidate_ids.add(candidate_id)
            owner = require_string(candidate.get("owner"), "owner", path)
            if owner not in SEMANTIC_OWNERS:
                raise EvalError(
                    f"{display_path(path)}: candidate owner must be one of {sorted(SEMANTIC_OWNERS)}"
                )
            if not isinstance(candidate.get("grounding_required"), bool):
                raise EvalError(
                    f"{display_path(path)}: candidate grounding_required must be boolean"
                )
            expected_action = require_string(
                candidate.get("expected_action"), "expected_action", path
            )
            if expected_action != EXPECTED_ACTION_BY_OWNER[owner]:
                raise EvalError(
                    f"{display_path(path)}: {candidate_id} owner {owner} requires action "
                    f"{EXPECTED_ACTION_BY_OWNER[owner]}, got {expected_action}"
                )
            if owner == "user-decision":
                user_decision_ids.add(candidate_id)

        expected_asked = data.get("expected_asked_candidates")
        if not isinstance(expected_asked, list) or not all(
            isinstance(item, str) and CANDIDATE_ID_RE.fullmatch(item)
            for item in expected_asked
        ):
            raise EvalError(
                f"{display_path(path)}: expected_asked_candidates must be a snake_case string list"
            )
        if len(expected_asked) != len(set(expected_asked)):
            raise EvalError(f"{display_path(path)}: expected_asked_candidates must be unique")
        unknown_asked = sorted(set(expected_asked) - user_decision_ids)
        if unknown_asked:
            raise EvalError(
                f"{display_path(path)}: expected question is not user-owned: "
                f"{', '.join(unknown_asked)}"
            )
        if case_id == ORDINARY_MATERIAL_CASE:
            if len(candidates) != 1 or expected_asked != ["public_cli_compatibility"]:
                raise EvalError(
                    f"{display_path(path)}: ordinary material clarification must define only "
                    "the public_cli_compatibility user decision"
                )

    if case_id in REQUIRED_ASK_PREDICATE_CASES:
        requires = data["expected"].get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: ask-predicate expected.requires must be a string list"
            )
        missing_coverage = sorted(REQUIRED_ASK_PREDICATE_CASES[case_id] - set(requires))
        if missing_coverage:
            raise EvalError(
                f"{display_path(path)}: ask-predicate coverage missing: "
                f"{', '.join(missing_coverage)}"
            )
        serialized = json.dumps(data, sort_keys=True).lower()
        retired_terms = (
            "task contract",
            "contract version",
            "finding state",
            "finding-state",
            "open blocker",
            "resolved finding",
            "waived finding",
        )
        present = [term for term in retired_terms if term in serialized]
        if present:
            raise EvalError(
                f"{display_path(path)}: retired lifecycle term remains: {', '.join(present)}"
            )

    if case_id in REQUIRED_SKILL_CASE_CLAUSES:
        requires = data["expected"].get("requires")
        if not isinstance(requires, list) or not all(
            isinstance(item, str) and item.strip() for item in requires
        ):
            raise EvalError(
                f"{display_path(path)}: skill contract expected.requires must be a string list"
            )
        normalized_requires = {normalize_contract_key(item) for item in requires}
        missing_skill_clauses = sorted(
            REQUIRED_SKILL_CASE_CLAUSES[case_id] - normalized_requires
        )
        if missing_skill_clauses:
            raise EvalError(
                f"{display_path(path)}: skill contract coverage missing: "
                f"{', '.join(missing_skill_clauses)}"
            )

    rubric = data.get("rubric")
    if rubric is not None:
        rubric_id = require_string(rubric, "rubric", path)
        if rubric_id not in known_rubrics:
            raise EvalError(f"{display_path(path)}: unknown rubric: {rubric_id}")
    return data


def validate_rubrics() -> set[str]:
    if not RUBRIC_DIR.is_dir():
        raise EvalError("evals/teamwork/rubrics/ is missing")
    rubrics: set[str] = set()
    for path in sorted(RUBRIC_DIR.glob("*.json")):
        data = load_json(path)
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(path)}: rubric must be a JSON object")
        rubric_id = require_string(data.get("id"), "id", path)
        if rubric_id in rubrics:
            raise EvalError(f"{display_path(path)}: duplicate rubric id: {rubric_id}")
        has_criteria = isinstance(data.get("criteria"), list) and bool(data["criteria"])
        has_dimensions = isinstance(data.get("dimensions"), list) and bool(data["dimensions"])
        if not has_criteria and not has_dimensions:
            raise EvalError(f"{display_path(path)}: rubric must define non-empty criteria or dimensions")
        if "description" in data:
            require_string(data.get("description"), "description", path)
        rubrics.add(rubric_id)
    if not rubrics:
        raise EvalError("no rubrics found")
    return rubrics


def validate_optimizer_candidate_entry(data: dict[str, Any], path: Path, index: int) -> None:
    kind = require_string(data.get("kind"), "kind", path)
    if kind not in OPTIMIZER_KINDS:
        raise EvalError(f"{display_path(path)}:{index}: kind must be one of {sorted(OPTIMIZER_KINDS)}")

    gate_decision = require_string(data.get("gate_decision"), "gate_decision", path)
    if gate_decision not in OPTIMIZER_GATE_DECISIONS:
        raise EvalError(
            f"{display_path(path)}:{index}: gate_decision must be one of {sorted(OPTIMIZER_GATE_DECISIONS)}"
        )

    decision = require_string(data.get("decision"), "decision", path)
    if decision not in OPTIMIZER_DECISIONS:
        raise EvalError(f"{display_path(path)}:{index}: decision must be one of {sorted(OPTIMIZER_DECISIONS)}")

    for field in (
        "candidate_id",
        "provider",
        "model",
        "model_config",
        "release_audit",
        "reviewer",
    ):
        item = require_string(data.get(field), field, path)
        if item == PLACEHOLDER:
            raise EvalError(f"{display_path(path)}:{index}: {field} must not be {PLACEHOLDER}")

    for field in ("prompt_or_template", "baseline", "treatment", "rollback"):
        require_evidence_path(data.get(field), field, path, index)

    owned_files = require_string_list(data.get("owned_files"), "owned_files", path)
    validate_owned_files(owned_files, path, index)

    for field in ("denylist", "validation"):
        items = require_string_list(data.get(field), field, path)
        if field == "validation" and all(item == PLACEHOLDER for item in items):
            raise EvalError(f"{display_path(path)}:{index}: validation must include real evidence")


def validate_ledger_lines(path: Path, name: str, required_fields: set[str]) -> int:
    if not path.is_file():
        raise EvalError(f"missing ledger: {display_path(path)}")
    lines = path.read_text().splitlines()
    if not lines:
        raise EvalError(f"{display_path(path)}: ledger must not be empty")
    line_count = 0
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{display_path(path)}:{index}: invalid JSONL: {exc}") from exc
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(path)}:{index}: ledger entry must be an object")
        require_string(data.get("date"), "date", path)
        missing = sorted(required_fields - set(data))
        if missing:
            raise EvalError(f"{display_path(path)}:{index}: missing ledger fields: {', '.join(missing)}")
        if name == "optimizer-candidates.jsonl":
            validate_optimizer_candidate_entry(data, path, index)
        line_count += 1
    return line_count


def validate_ledgers() -> int:
    if not LEDGER_DIR.is_dir():
        raise EvalError("evals/teamwork/ledgers/ is missing")
    line_count = 0
    for name, required_fields in sorted(LEDGER_SCHEMAS.items()):
        path = LEDGER_DIR / name
        if not path.is_file():
            if name == "optimizer-candidates.jsonl":
                continue
            raise EvalError(f"missing ledger: {display_path(path)}")
        line_count += validate_ledger_lines(path, name, required_fields)
    return line_count


def validate_output_trajectory(value: Any, path: Path, index: int) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise EvalError(f"{display_path(path)}:{index}: trajectory must be a non-empty list")
    turns: list[dict[str, Any]] = []
    for turn_index, turn in enumerate(value, start=1):
        if not isinstance(turn, dict) or not {"user", "assistant"}.issubset(turn):
            raise EvalError(
                f"{display_path(path)}:{index}: trajectory turn {turn_index} must contain user and assistant"
            )
        unknown = sorted(set(turn) - {"user", "assistant", "asked_candidates"})
        if unknown:
            raise EvalError(
                f"{display_path(path)}:{index}: trajectory turn {turn_index} has unknown fields: "
                f"{', '.join(unknown)}"
            )
        user = require_string(turn.get("user"), "trajectory.user", path)
        assistant = require_string(turn.get("assistant"), "trajectory.assistant", path)
        asked = turn.get("asked_candidates", [])
        if not isinstance(asked, list) or not all(
            isinstance(item, str) and CANDIDATE_ID_RE.fullmatch(item) for item in asked
        ):
            raise EvalError(
                f"{display_path(path)}:{index}: trajectory turn {turn_index} "
                "asked_candidates must be a snake_case string list"
            )
        turns.append({"user": user, "assistant": assistant, "asked_candidates": asked})
    return turns


def is_public_cli_compatibility_question(text: str) -> bool:
    question_marks = [match.start() for match in re.finditer(r"[?？]", text)]
    if len(question_marks) != 1:
        return False
    mark_index = question_marks[0]
    sentence_boundaries = (".", "!", "！", "?", "？", "\n")
    sentence_start = max(
        (text.rfind(boundary, 0, mark_index) for boundary in sentence_boundaries),
        default=-1,
    )
    lowered = text[sentence_start + 1 : mark_index + 1].lower()
    public_cli = bool(re.search(r"\bpublic\b", lowered)) and bool(
        re.search(r"\b(?:cli|command)\b", lowered)
    )
    compatibility = bool(
        re.search(r"\bcompatib\w*\b", lowered)
        or re.search(r"\b(?:keep|continue)\w*\s+(?:to\s+)?work(?:ing)?\b", lowered)
        or re.search(
            r"\bexisting scripts?\b.{0,48}\b(?:work\w*|break\w*|migrat\w*|preserv\w*|support\w*)\b",
            lowered,
        )
        or re.search(
            r"\b(?:work\w*|break\w*|migrat\w*|preserv\w*|support\w*)\b.{0,48}\bexisting scripts?\b",
            lowered,
        )
    )
    return public_cli and compatibility


def validate_question_first_outputs(cases_by_id: dict[str, dict[str, Any]]) -> int:
    case_ids = set(cases_by_id)
    missing_cases = sorted(set(REQUIRED_QUESTION_FIRST_CASES) - case_ids)
    if missing_cases:
        raise EvalError(f"missing question-first case(s): {', '.join(missing_cases)}")

    output_path = OUTPUT_DIR / "question-first" / "dev.jsonl"
    if not output_path.is_file():
        raise EvalError(f"missing question-first output samples: {display_path(output_path)}")

    seen: set[str] = set()
    seen_platforms: dict[str, set[str]] = {case_id: set() for case_id in REQUIRED_QUESTION_FIRST_CASES}
    rows = 0
    for index, line in enumerate(output_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{display_path(output_path)}:{index}: invalid JSONL: {exc}") from exc
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(output_path)}:{index}: output row must be an object")
        missing = sorted(OUTPUT_REQUIRED_FIELDS - set(data))
        if missing:
            raise EvalError(f"{display_path(output_path)}:{index}: missing output fields: {', '.join(missing)}")

        case_id = require_string(data.get("case_id"), "case_id", output_path)
        if case_id not in REQUIRED_QUESTION_FIRST_CASES:
            raise EvalError(f"{display_path(output_path)}:{index}: unexpected question-first case_id: {case_id}")
        if case_id not in case_ids:
            raise EvalError(f"{display_path(output_path)}:{index}: output references missing case: {case_id}")
        case = cases_by_id[case_id]

        platforms = set(require_string_list(data.get("platforms"), "platforms", output_path))
        unknown_platforms = sorted(platforms - PLATFORMS)
        if unknown_platforms:
            raise EvalError(
                f"{display_path(output_path)}:{index}: unknown platform(s): {', '.join(unknown_platforms)}"
            )
        input_text = require_string(data.get("input"), "input", output_path)
        output_text = require_string(data.get("output"), "output", output_path)
        trajectory = validate_output_trajectory(data.get("trajectory"), output_path, index)
        if trajectory[0]["user"] != input_text:
            raise EvalError(f"{display_path(output_path)}:{index}: input must match the first trajectory user turn")
        if trajectory[-1]["assistant"] != output_text:
            raise EvalError(f"{display_path(output_path)}:{index}: output must match the final trajectory assistant turn")

        expected = set(require_string_list(data.get("expected_behavior"), "expected_behavior", output_path))
        required = REQUIRED_QUESTION_FIRST_CASES[case_id]
        missing_expected = sorted(required - expected)
        if missing_expected:
            raise EvalError(
                f"{display_path(output_path)}:{index}: expected_behavior missing for {case_id}: "
                f"{', '.join(missing_expected)}"
            )

        passed = data.get("passed")
        if not isinstance(passed, bool):
            raise EvalError(f"{display_path(output_path)}:{index}: passed must be boolean")
        fail_reason = data.get("fail_reason")
        if not isinstance(fail_reason, str):
            raise EvalError(f"{display_path(output_path)}:{index}: fail_reason must be a string")
        if passed and fail_reason:
            raise EvalError(f"{display_path(output_path)}:{index}: passing row must have empty fail_reason")
        if not passed:
            raise EvalError(f"{display_path(output_path)}:{index}: question-first sample failed: {fail_reason}")
        evidence_tier = data.get("evidence_tier", STATIC_FIXTURE_EVIDENCE_TIER)
        if evidence_tier != STATIC_FIXTURE_EVIDENCE_TIER:
            raise EvalError(
                f"{display_path(output_path)}:{index}: authored trajectory may only declare "
                f"evidence_tier={STATIC_FIXTURE_EVIDENCE_TIER!r}; it is not live model evidence"
            )

        output = output_text.lower()
        if case_id in SEMANTIC_QUESTION_CASES:
            observed_asked: list[str] = []
            for turn_index, turn in enumerate(trajectory, start=1):
                assistant = turn["assistant"]
                asked = turn["asked_candidates"]
                marks = question_count(assistant)
                if len(asked) > 1 or marks > 1:
                    raise EvalError(
                        f"{display_path(output_path)}:{index}: turn {turn_index} asks more than one decision"
                    )
                if bool(asked) != (marks == 1):
                    raise EvalError(
                        f"{display_path(output_path)}:{index}: turn {turn_index} question text and "
                        "asked_candidates annotation disagree"
                    )
                if has_legacy_grill_ceremony(assistant):
                    raise EvalError(
                        f"{display_path(output_path)}:{index}: turn {turn_index} exposes "
                        "the superseded grill packet/state protocol"
                    )
                if SEMANTIC_ENACTMENT_RE.search(assistant):
                    raise EvalError(
                        f"{display_path(output_path)}:{index}: turn {turn_index} enacts work "
                        "inside the question-first fixture"
                    )
                if AUTHORITY_GRANT_RE.search(assistant):
                    raise EvalError(
                        f"{display_path(output_path)}:{index}: turn {turn_index} invents "
                        "implementation authority"
                    )
                observed_asked.extend(asked)
            expected_asked = case["expected_asked_candidates"]
            if observed_asked != expected_asked:
                raise EvalError(
                    f"{display_path(output_path)}:{index}: asked candidates {observed_asked} "
                    f"do not match semantic oracle {expected_asked}"
                )
            if case_id == "grill-fact-lookup":
                if not any(
                    "skills/ and install.sh inventories" in turn["assistant"]
                    for turn in trajectory
                ):
                    raise EvalError(f"{display_path(output_path)}:{index}: fact lookup fixture lacks bounded evidence")
            if case_id == "grill-question-value-stop":
                validate_mainline_distraction_output(case, trajectory, output_path, index)
        if case_id in GRILL_CONTROL_CASES:
            assistant_text = "\n".join(turn["assistant"].lower() for turn in trajectory)
            if has_legacy_grill_ceremony(assistant_text):
                raise EvalError(f"{display_path(output_path)}:{index}: inert control emitted grill ceremony")
            if any(question_count(turn["assistant"]) for turn in trajectory):
                raise EvalError(f"{display_path(output_path)}:{index}: inert marker control asked a grill question")
        if case_id == "question-first-complex-uncertainty":
            if question_count(output_text) != 1:
                raise EvalError(f"{display_path(output_path)}:{index}: complex uncertainty output must ask a question")
            if "steps:" in output or "implementation" in output:
                raise EvalError(f"{display_path(output_path)}:{index}: complex uncertainty output planned before asking")
        if case_id == "question-first-lightweight-control":
            ceremony_forbidden = (
                "grill status:",
                "grill",
                "question-first",
            )
            orchestration_forbidden = (
                "question:",
                "dispatch",
                "subagent",
                "worker",
                "durable plan",
                "plan:",
                "planning",
                "tool call",
                "code executor",
                "shell",
                "terminal",
            )
            if "?" in data["output"] or any(item in output for item in ceremony_forbidden):
                raise EvalError(f"{display_path(output_path)}:{index}: lightweight output must not use grill ceremony")
            if any(item in output for item in orchestration_forbidden):
                raise EvalError(f"{display_path(output_path)}:{index}: lightweight output must not plan or dispatch")
            direct_markers = ("directly", "make the one-line", "fix the typo")
            if not any(item in output for item in direct_markers):
                raise EvalError(f"{display_path(output_path)}:{index}: lightweight output must indicate direct action")
        if case_id == "complex-autonomy-control":
            forbidden = (
                "question:",
                "grill status:",
                "grill",
                "question-first",
                "which do you prefer",
                "would you like",
            )
            if "?" in data["output"] or any(item in output for item in forbidden):
                raise EvalError(
                    f"{display_path(output_path)}:{index}: autonomy control must not ask or add grill ceremony"
                )
            proceed_markers = ("inspect", "proceed", "design", "implement")
            if not any(item in output for item in proceed_markers):
                raise EvalError(
                    f"{display_path(output_path)}:{index}: autonomy control must indicate inspection and action"
                )
        if case_id == ORDINARY_MATERIAL_CASE:
            if len(trajectory) != 1:
                raise EvalError(
                    f"{display_path(output_path)}:{index}: ordinary material clarification "
                    "must contain exactly one assistant turn"
                )
            question_marks = question_count(output_text)
            if question_marks != 1:
                raise EvalError(
                    f"{display_path(output_path)}:{index}: ordinary material clarification "
                    "must contain exactly one question mark"
                )
            if has_legacy_grill_ceremony(output_text):
                raise EvalError(
                    f"{display_path(output_path)}:{index}: ordinary material clarification "
                    "must not emit grill packet/state ceremony"
                )
            if re.search(
                r"(?im)^\s*(?:question|recommended|options|other):",
                output_text,
            ) or len(re.findall(r"(?m)^\s*[-*]\s+\S+", output_text)) >= 2:
                raise EvalError(
                    f"{display_path(output_path)}:{index}: ordinary material clarification "
                    "must be one concise question, not a choice card"
                )
            if ORDINARY_ACTION_RE.search(output_text):
                raise EvalError(
                    f"{display_path(output_path)}:{index}: ordinary material clarification "
                    "must not plan, edit, or enact the change"
                )
            if not is_public_cli_compatibility_question(output_text):
                raise EvalError(
                    f"{display_path(output_path)}:{index}: ordinary material clarification "
                    "must ask the public CLI compatibility question"
                )

        seen.add(case_id)
        seen_platforms[case_id].update(platforms)
        rows += 1

    missing_outputs = sorted(set(REQUIRED_QUESTION_FIRST_CASES) - seen)
    if missing_outputs:
        raise EvalError(f"missing question-first output row(s): {', '.join(missing_outputs)}")
    for case_id, platforms in sorted(seen_platforms.items()):
        missing_platforms = sorted(PLATFORMS - platforms)
        if missing_platforms:
            raise EvalError(
                f"missing question-first output platform(s) for {case_id}: {', '.join(missing_platforms)}"
            )
    return rows


def selected_cases(selection: str) -> list[dict[str, Any]]:
    validate_semantic_sources()
    if not CASE_DIR.is_dir():
        raise EvalError("evals/teamwork/cases/ is missing")
    known_rubrics = validate_rubrics()
    validate_ledgers()
    cases = [validate_case(path, known_rubrics) for path in sorted(CASE_DIR.glob("*.json"))]
    if not cases:
        raise EvalError("no cases found")
    seen: set[str] = set()
    cases_by_id: dict[str, dict[str, Any]] = {}
    for case in cases:
        case_id = case["id"]
        if case_id in seen:
            raise EvalError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        cases_by_id[case_id] = case
    missing_ask_cases = sorted(set(REQUIRED_ASK_PREDICATE_CASES) - seen)
    if missing_ask_cases:
        raise EvalError(f"missing ask-predicate case(s): {', '.join(missing_ask_cases)}")
    missing_minimality_cases = sorted(set(REQUIRED_MINIMALITY_CASES) - seen)
    if missing_minimality_cases:
        raise EvalError(
            f"missing minimality case(s): {', '.join(missing_minimality_cases)}"
        )
    missing_semantic_init_cases = sorted(set(REQUIRED_SEMANTIC_INIT_CASES) - seen)
    if missing_semantic_init_cases:
        raise EvalError(
            "missing semantic-init case(s): " + ", ".join(missing_semantic_init_cases)
        )
    missing_discussion_cases = sorted(set(REQUIRED_DISCUSSION_CASES) - seen)
    if missing_discussion_cases:
        raise EvalError(
            "missing discussion case(s): " + ", ".join(missing_discussion_cases)
        )
    missing_activation_cases = sorted(set(REQUIRED_ACTIVATION_CASES) - seen)
    if missing_activation_cases:
        raise EvalError(
            "missing weak-cue case(s): " + ", ".join(missing_activation_cases)
        )
    for skill, required_cases in REQUIRED_SKILL_CONTRACT_CASES.items():
        missing_skill_cases = sorted(required_cases - seen)
        if missing_skill_cases:
            raise EvalError(
                f"missing {skill} contract case(s): {', '.join(missing_skill_cases)}"
            )
    output_rows = validate_question_first_outputs(cases_by_id)
    if selection == "all":
        selected = cases
        missing_splits = sorted(split for split in SPLITS if not any(case["split"] == split for case in cases))
        if missing_splits:
            raise EvalError(f"empty split(s): {', '.join(missing_splits)}")
    else:
        selected = [case for case in cases if case["split"] == selection]
    if not selected:
        raise EvalError(f"split {selection!r} has no cases")
    return selected
