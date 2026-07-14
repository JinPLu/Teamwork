#!/usr/bin/env python3
"""Validate Teamwork eval fixtures without network or model dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from grill_contract import (
    has_legacy_grill_ceremony,
    question_count,
)

ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "evals" / "teamwork"
CASE_DIR = EVAL_ROOT / "cases"
RUBRIC_DIR = EVAL_ROOT / "rubrics"
LEDGER_DIR = EVAL_ROOT / "ledgers"
OUTPUT_DIR = Path(os.environ.get("TEAMWORK_EVAL_OUTPUT_DIR", EVAL_ROOT / "outputs"))

REQUIRED_CASE_FIELDS = {
    "id",
    "split",
    "source",
    "target",
    "platforms",
    "prompt",
    "expected",
    "must",
    "must_not",
    "evidence",
}
SPLITS = {"dev", "release"}
SOURCES = {"synthetic", "trajectory", "bug", "review", "release"}
PLATFORMS = {"codex", "cursor", "claude"}
TARGET_PREFIXES = ("skills/", "evals/teamwork/", "scripts/eval-teamwork.py")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CANDIDATE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
LEDGER_SCHEMAS = {
    "accepted.jsonl": {
        "date",
        "change_id",
        "surface",
        "decision",
        "reason",
        "cases",
        "validation",
        "reviewer",
    },
    "rejected.jsonl": {
        "date",
        "proposal",
        "surface",
        "reason",
        "risk",
        "replacement",
    },
    "harness-candidates.jsonl": {
        "date",
        "candidate_id",
        "owned_files",
        "hypothesis",
        "baseline",
        "candidate_result",
        "decision",
        "rollback",
    },
    "optimizer-candidates.jsonl": {
        "date",
        "candidate_id",
        "kind",
        "provider",
        "model",
        "model_config",
        "prompt_or_template",
        "owned_files",
        "denylist",
        "baseline",
        "treatment",
        "gate_decision",
        "rollback",
        "validation",
        "release_audit",
        "reviewer",
        "decision",
    },
}
OPTIMIZER_KINDS = {"skillopt-lite", "harnessopt-lite"}
OPTIMIZER_GATE_DECISIONS = {"accept_new_best", "accept", "reject", "flat", "blocked"}
OPTIMIZER_DECISIONS = {"candidate", "accepted", "rejected", "blocked"}
PLACEHOLDER = "not_applicable"
GLOB_CHARS = set("*?[")
REQUIRED_QUESTION_FIRST_CASES = {
    "complex-autonomy-control": {
        "inspect_and_proceed",
        "no_grill_ceremony",
        "no_question",
    },
    "question-first-explicit-grill": {
        "material_question",
        "ownership_oracle",
        "no_legacy_ceremony",
        "no_enactment",
    },
    "question-first-explicit-lightweight-grill": {
        "zero_questions",
        "agent_owned_choices",
        "authority_preserved",
        "no_legacy_ceremony",
        "no_padding",
    },
    "question-first-complex-uncertainty": {
        "decision_risk_question",
        "native_when_callable",
        "teamwork_plan_quality_gate",
        "sourced_critical_values",
        "no_plan_before_question",
    },
    "question-first-lightweight-control": {
        "direct_lightweight",
        "no_grill_ceremony",
        "no_subagent_dispatch",
        "no_durable_plan",
        "no_question",
    },
    "ordinary-material-clarification-control": {
        "ordinary_clarification",
        "material_user_decision",
        "no_grill_ceremony",
        "no_enactment",
    },
    "grill-explicit-skill-invocation": {
        "material_question",
        "no_legacy_ceremony",
        "no_enactment",
    },
    "grill-chinese-explicit-intent": {
        "material_question",
        "chinese_explicit_activation",
        "no_legacy_ceremony",
        "no_enactment",
    },
    "grill-multiturn-continuation-exit": {
        "multiturn_continuation",
        "question_order",
        "authority_preserved",
        "no_enactment",
    },
    "grill-fact-lookup": {
        "facts_checked",
        "material_question",
    },
    "grill-question-value-stop": {
        "ownership_oracle",
        "expected_asked_candidates",
        "normal_completion",
        "no_new_authority",
    },
    "grill-zero-question-low-value": {
        "zero_questions",
        "agent_owned_choices",
        "no_new_authority",
    },
    "grill-task-replacement": {
        "old_task_stops",
        "no_new_authority",
        "task_replacement",
    },
    "grill-language-ownership-contrast": {"ownership_contrast", "expected_asked_candidates"},
    "grill-rename-ownership-contrast": {"ownership_contrast", "expected_asked_candidates"},
    "grill-boundary-ownership-contrast": {"ownership_contrast", "expected_asked_candidates"},
    "grill-observable-preference-contrast": {"ownership_contrast", "expected_asked_candidates"},
    "grill-threshold-evidence-contrast": {"evidence_owned", "zero_questions"},
    "grill-reversibility-ownership-contrast": {"ownership_contrast", "expected_asked_candidates"},
    "grill-quoted-marker-control": {"quoted_marker_inert", "no_grill_ceremony"},
    "grill-file-tool-marker-control": {"file_tool_marker_inert", "no_grill_ceremony"},
    "grill-maintenance-marker-control": {"maintenance_not_activation", "no_grill_ceremony"},
    "grill-negative-signal-control": {"negative_signal_wins", "no_grill_ceremony"},
}
REQUIRED_ASK_PREDICATE_CASES = {
    "ask-native-simple-control": {"simple_native", "zero_questions"},
    "ask-discoverable-fact-control": {"discoverable_fact", "zero_questions"},
    "ask-required-input-research": {"research_stage", "required_input", "ask_outside_grill"},
    "ask-required-observation-debug": {"debug_stage", "required_observation", "ask_outside_grill"},
    "ask-required-input-execute": {"execute_stage", "required_input", "ask_outside_grill"},
    "ask-required-observation-review": {"review_stage", "required_observation", "ask_outside_grill"},
    "ask-required-input-goal": {"goal_stage", "required_input", "ask_outside_grill"},
    "plan-ask-readiness": {"non_simple_auto_grill", "decision_summary", "no_execution_authority"},
    "review-bounded-recheck": {"stable_finding_ids", "review_taxonomy", "blocker_classification", "one_corrective_recheck"},
    "goal-dependent-branch-retry": {"affected_branch_only", "independent_work_continues", "native_goal_authority"},
    "ask-confirmation-authority": {"confirmation_only", "no_implementation_authority", "no_release_authority"},
    "ask-subagent-root-ownership": {"question_candidate", "root_only_asks", "deduplicate"},
    "ask-independent-readonly-progress": {"dependent_branch_only", "independent_read_only_continues"},
    "ask-text-fallback": {"native_unavailable", "concise_text_fallback"},
}
REQUIRED_WORKING_FACTS_CASES = {
    "working-facts-scope-correction": {
        "working_facts_update",
        "dependent_work_pauses",
        "stale_delegated_results_discarded",
    },
}
REQUIRED_MINIMALITY_CASES = {
    "minimality-canonical-reuse": {
        "canonical_owner",
        "boundary_builtin_or_dependency",
        "minimal_new_logic",
        "proportional_proof",
    },
    "minimality-justified-surface": {
        "accepted_behavior_justifies_new_logic",
        "justified_abstraction_or_dependency",
        "multi_file_allowed",
        "proportional_proof",
        "no_code_golf",
    },
    "minimality-review-classification": {
        "minimality_reviewable",
        "acceptance_failure_blocker",
        "non_ac_cleanup_follow_up_or_suggestion",
        "no_scope_expansion",
    },
}
REQUIRED_SKILL_CASE_CLAUSES = {
    "native-lightweight-control": {"complete_stage_inventory", "native_fast_path"},
    "grill-explicit-skill-invocation": {"explicit_activation", "no_enactment"},
    "grill-negative-signal-control": {"negative_signal_wins", "no_activation"},
    "grill-quoted-marker-control": {"quoted_marker_inert", "no_activation"},
    "grill-question-value-stop": {"no_implementation_authority"},
    "research-source-quality": {"observed_inferred_claimed", "read_only_boundary"},
    "debug-repro-before-fix": {
        "repro_before_fix",
        "discriminating_hypotheses",
        "safe_fix_route",
    },
    "plan-ask-readiness": {
        "non_simple_auto_grill",
        "decision_summary",
        "no_execution_authority",
    },
    "complex-coding-discipline": {
        "accepted_scope",
        "discovery_classification",
        "failed_ac_monotonicity",
    },
    "review-bounded-recheck": {
        "review_taxonomy",
        "risk_gated_fresh_review",
        "one_corrective_recheck",
    },
    "goal-dependent-branch-retry": {
        "native_goal_authority",
        "preserved_invariants",
        "strategy_delta",
        "affected_branch_only",
    },
    "init-readiness-contract": {
        "readiness_gaps_reported",
        "safe_local_continuation",
        "host_tools_host_owned",
        "external_tooling_approval",
    },
    "update-release-ledger": {
        "version_canonical",
        "publication_authority",
        "release_ready_until_tag_and_github_release",
    },
}
SKILL_SOURCE_CONTRACTS = {
    "using-teamwork": (
        "skills/using-teamwork/SKILL.md",
        (
            ("Native fast path", "small, clear tasks stay native"),
            ("Native stage", "**Native**"),
            ("Research stage", "**Research**"),
            ("Debug stage", "**Debug**"),
            ("Plan stage", "**Plan**"),
            ("Execute stage", "**Execute**"),
            ("Review stage", "**Review**"),
            ("Goal stage", "**Goal**"),
            ("Init stage", "**Init**"),
            ("Update stage", "**Update**"),
        ),
    ),
    "grill-me": (
        "skills/grill-me/SKILL.md",
        (
            ("explicit activation", "enter for an explicit request"),
            ("negative intent wins", "explicit negative intent suppresses this interview"),
            ("inert mentions", "quoted, file, tool, example, or maintenance mentions are inert"),
            ("no execution authority", "confirmation does not grant implementation authority"),
        ),
    ),
    "teamwork-research": (
        "skills/teamwork-research/SKILL.md",
        (
            ("observed/inferred/claimed evidence", "`observed`, `inferred`, and `claimed` findings"),
            ("read-only boundary", "research does not authorize edits, external writes"),
        ),
    ),
    "teamwork-debug": (
        "skills/teamwork-debug/SKILL.md",
        (
            ("repro before fix", "state expected versus actual behavior, the repro"),
            ("discriminating hypotheses", "name discriminating evidence"),
            ("safe fix route", "route an accepted fix to execution"),
        ),
    ),
    "teamwork-plan": (
        "skills/teamwork-plan/SKILL.md",
        (
            ("non-simple material Grill", "every non-simple plan enters evidence-first `grill-me`"),
            ("Decision Summary", "needs a confirmed decision summary"),
            ("no execution authority", "confirmation grants no implementation, release, external-effect, or other authority"),
        ),
    ),
    "teamwork-execute": (
        "skills/teamwork-execute/SKILL.md",
        (
            ("accepted scope", "use when an accepted plan, scope, or known root-cause fix"),
            ("discovery classification", "classify discoveries:"),
            ("failed-AC monotonicity", "failed ac evidence stays failed until direct evidence changes that ac"),
        ),
    ),
    "teamwork-review": (
        "skills/teamwork-review/SKILL.md",
        (
            ("review taxonomy must be BLOCKER, FOLLOW-UP, or SUGGESTION", "one class: `blocker`, `follow-up`, or `suggestion`"),
            ("risk-gated fresh review", "fresh context is required for high-risk, public-contract, delegated, security, destructive, release, or goal acceptance"),
            ("one bounded recheck", "permit one corrective recheck"),
        ),
    ),
    "teamwork-goal": (
        "skills/teamwork-goal/SKILL.md",
        (
            ("explicit user request or accepted Goal Proposal", "only when the user explicitly requests goal mode or accepts a goal proposal"),
            ("preserved Goal Invariants", "identify the preserved scope/invariants, failed claim and stage, prior evidence, do-not-repeat constraints"),
            ("strategy delta", "stop on repeated no-progress without an evidence-backed strategy delta"),
            ("affected stage", "route only the affected stage"),
        ),
    ),
    "teamwork-init": (
        "skills/teamwork-init/SKILL.md",
        (
            ("readiness gaps", "reported gaps, not stop conditions"),
            ("safe local continuation", "project surfaces continue even when the global install returns an actionable configuration failure"),
            ("host-owned tools", "native interaction tools are host capabilities, not teamwork installation requirements"),
            ("external tooling approval", "do not install external tooling without approval"),
        ),
    ),
    "teamwork-update": (
        "skills/teamwork-update/SKILL.md",
        (
            ("VERSION canonical", "`version` is the source of truth"),
            ("publication authority", "with explicit publication authority"),
            ("release-ready until tag and GitHub Release", "until the tag and github release exist, report `release-ready`, not `released`"),
        ),
    ),
}
RETIRED_ACTIVE_CASE_TERMS = (
    "stage entry card",
    "truth identity",
    "frozen card",
    "scope delta gate",
)
GRILL_SEMANTIC_CASES = {
    "question-first-explicit-grill",
    "question-first-explicit-lightweight-grill",
    "grill-explicit-skill-invocation",
    "grill-chinese-explicit-intent",
    "grill-multiturn-continuation-exit",
    "grill-fact-lookup",
    "grill-question-value-stop",
    "grill-zero-question-low-value",
    "grill-task-replacement",
    "grill-language-ownership-contrast",
    "grill-rename-ownership-contrast",
    "grill-boundary-ownership-contrast",
    "grill-observable-preference-contrast",
    "grill-threshold-evidence-contrast",
    "grill-reversibility-ownership-contrast",
}
ORDINARY_MATERIAL_CASE = "ordinary-material-clarification-control"
SEMANTIC_QUESTION_CASES = GRILL_SEMANTIC_CASES | {ORDINARY_MATERIAL_CASE}
GRILL_CONTROL_CASES = {
    "grill-quoted-marker-control",
    "grill-file-tool-marker-control",
    "grill-maintenance-marker-control",
    "grill-negative-signal-control",
}
REQUIRED_SKILL_CONTRACT_CASES = {
    "using-teamwork": {"native-lightweight-control"},
    "grill-me": GRILL_SEMANTIC_CASES
    | GRILL_CONTROL_CASES
    | {"question-first-explicit-grill", "question-first-explicit-lightweight-grill"},
    "teamwork-research": {"research-source-quality"},
    "teamwork-debug": {"debug-repro-before-fix"},
    "teamwork-plan": {"plan-ask-readiness"},
    "teamwork-execute": {"complex-coding-discipline"},
    "teamwork-review": {"review-bounded-recheck"},
    "teamwork-goal": {"goal-dependent-branch-retry"},
    "teamwork-init": {"init-readiness-contract"},
    "teamwork-update": {"update-release-ledger"},
}
SEMANTIC_OWNERS = {"evidence", "agent", "user-decision", "required-input", "confirmation"}
EXPECTED_ACTION_BY_OWNER = {
    "evidence": "resolve",
    "agent": "decide",
    "user-decision": "ask",
    "required-input": "request-input",
    "confirmation": "confirm-later",
}
OUTPUT_REQUIRED_FIELDS = {
    "case_id",
    "platforms",
    "input",
    "output",
    "trajectory",
    "expected_behavior",
    "passed",
    "fail_reason",
}
STATIC_FIXTURE_EVIDENCE_TIER = "static-authored-contract-fixture"
ORDINARY_ACTION_RE = re.compile(
    r"(?im)(?:"
    r"\b(?:plan|planning|steps?|edit(?:ed|ing|s)?|implement(?:ation|ed|ing|s)?|"
    r"enact(?:ment|ed|ing|s)?|execut(?:e|ed|ing|ion|es)|proceed(?:ed|ing|s)?|"
    r"updat(?:e|ed|ing|es)|modif(?:y|ied|ying|ies)|creat(?:e|ed|ing|es)|"
    r"delet(?:e|ed|ing|es)|wrote|written)\b"
    r"|^\s*(?:edited|changed|implemented|updated|modified|wrote|created|deleted)\b"
    r"|\b(?:i|we)(?:\s+have|'ve)?\s+"
    r"(?:edited|changed|implemented|renamed|updated|modified|wrote|created|deleted)\b"
    r"|\b(?:i|we)\s+(?:will|shall|am going to|are going to)\s+"
    r"(?:edit|change|implement|rename|update|modify|write|create|delete|execute|proceed)\b"
    r")"
)
SEMANTIC_ENACTMENT_RE = re.compile(
    r"(?i)\b(?:i|we)(?:\s+have|'ve|\s+will|\s+shall|\s+am going to|\s+are going to)\s+"
    r"(?:edit|change|implement|rename|update|modify|write|create|delete|execute|proceed)\b"
)
AUTHORITY_GRANT_RE = re.compile(
    r"(?i)\b(?:implementation\s+)?authority\s+(?:is\s+)?granted\b|"
    r"\b(?:now\s+)?authorized\s+to\s+(?:edit|implement|execute|proceed)\b"
)


class EvalError(Exception):
    pass


def normalize_semantic_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def validate_skill_source_contract(skill: str, source_text: str) -> None:
    path, clauses = SKILL_SOURCE_CONTRACTS[skill]
    normalized = normalize_semantic_text(source_text)
    for label, clause in clauses:
        if normalize_semantic_text(clause) not in normalized:
            raise EvalError(f"{path}: skill contract must preserve {label}")


def validate_semantic_source_text(
    review_text: str, goal_text: str, role_playbook_text: str
) -> None:
    validate_skill_source_contract("teamwork-review", review_text)
    if re.search(
        r"(?i)one class:\s*`blocker`\s*,\s*`major`\s*,\s*(?:or\s*)?`minor`",
        review_text,
    ):
        raise EvalError(
            "skills/teamwork-review/SKILL.md: retired blocker/major/minor taxonomy remains"
        )

    role_taxonomy = "`BLOCKER | FOLLOW-UP | SUGGESTION` findings"
    if role_taxonomy not in role_playbook_text:
        raise EvalError(
            "skills/using-teamwork/references/role-playbook.md: review taxonomy must be "
            "BLOCKER | FOLLOW-UP | SUGGESTION"
        )
    if re.search(
        r"(?i)`blocker\s*\|\s*major\s*\|\s*minor`",
        role_playbook_text,
    ):
        raise EvalError(
            "skills/using-teamwork/references/role-playbook.md: retired "
            "blocker | major | minor taxonomy remains"
        )

    validate_skill_source_contract("teamwork-goal", goal_text)
    normalized_goal = normalize_semantic_text(goal_text)
    if re.search(r"(?i)native goal state.{0,80}when available", normalized_goal):
        raise EvalError(
            "skills/teamwork-goal/SKILL.md: native goal state must not activate merely "
            "when available"
        )


def validate_minimality_source_text(
    workflow_contract_text: str, review_lenses_text: str
) -> None:
    workflow = " ".join(workflow_contract_text.split())
    review_lenses = " ".join(review_lenses_text.split())
    for anchor in (
        "the canonical owner/pattern, language or host/platform built-ins, a "
        "boundary-appropriate installed dependency, then minimal new logic",
        "not fewer lines or files",
        "Never trade away clarity, correctness, security, accessibility, portability, "
        "accepted behavior, or proportional verification",
    ):
        if anchor not in workflow:
            raise EvalError(
                "skills/using-teamwork/references/workflow-contract.md: minimality "
                f"boundary must preserve {anchor}"
            )
    for anchor in (
        "unaccepted cleanup as `SUGGESTION` or `out_of_scope`, not as a reason to "
        "expand the candidate",
        "Do not score minimality by LOC or file count",
        "Justified abstractions, dependencies, and multi-file changes are not slop "
        "when they improve cost without weakening proof",
    ):
        if anchor not in review_lenses:
            raise EvalError(
                "skills/using-teamwork/references/review-lenses.md: minimality review "
                f"boundary must preserve {anchor}"
            )


def validate_semantic_sources() -> None:
    for skill, (path, _) in SKILL_SOURCE_CONTRACTS.items():
        if skill in {"teamwork-review", "teamwork-goal"}:
            continue
        validate_skill_source_contract(
            skill,
            (ROOT / path).read_text(encoding="utf-8"),
        )
    validate_semantic_source_text(
        (ROOT / "skills/teamwork-review/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/teamwork-goal/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/references/role-playbook.md").read_text(
            encoding="utf-8"
        ),
    )
    validate_minimality_source_text(
        (ROOT / "skills/using-teamwork/references/workflow-contract.md").read_text(
            encoding="utf-8"
        ),
        (ROOT / "skills/using-teamwork/references/review-lenses.md").read_text(
            encoding="utf-8"
        ),
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Teamwork eval fixtures.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--split", choices=sorted(SPLITS))
    group.add_argument("--all", action="store_true", help="validate all cases")
    group.add_argument("--optimizer-ledger", type=Path, metavar="PATH", help="validate one optimizer candidate ledger")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.optimizer_ledger:
        path = args.optimizer_ledger.resolve()
        try:
            count = validate_ledger_lines(path, "optimizer-candidates.jsonl", LEDGER_SCHEMAS["optimizer-candidates.jsonl"])
        except EvalError as exc:
            print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"status": "pass", "selection": "optimizer-ledger", "rows": count}, sort_keys=True))
        print(f"OK: optimizer ledger passed ({count} rows)")
        return 0

    selection = "all" if args.all else args.split
    try:
        cases = selected_cases(selection)
    except EvalError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    by_split = {split: 0 for split in SPLITS}
    by_platform = {platform: 0 for platform in PLATFORMS}
    for case in cases:
        by_split[case["split"]] += 1
        for platform in case["platforms"]:
            by_platform[platform] += 1
    detail = ", ".join(f"{split}={count}" for split, count in sorted(by_split.items()) if count)
    summary = {
        "status": "pass",
        "selection": selection,
        "cases": len(cases),
        "by_split": {split: count for split, count in sorted(by_split.items()) if count},
        "by_platform": {platform: count for platform, count in sorted(by_platform.items()) if count},
        "case_ids": [case["id"] for case in cases],
    }
    print(json.dumps(summary, sort_keys=True))
    print(f"OK: Teamwork eval {selection} passed ({len(cases)} cases; {detail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
