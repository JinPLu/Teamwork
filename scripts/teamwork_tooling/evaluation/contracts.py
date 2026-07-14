"""Paths, schemas, and validation contracts for deterministic Teamwork evals."""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
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
TARGET_PREFIXES = ("skills/", "evals/teamwork/", "scripts/eval-teamwork.py", "AGENTS.md")
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
REQUIRED_SEMANTIC_INIT_CASES = {
    "init-semantic-project-model": {
        "separate_audit_bootstrap_semantic",
        "explicit_init_defaults_to_semantic",
        "project_model_before_edits",
        "six_way_classification",
        "cross_platform_instruction_ownership",
        "human_docs_preserved",
        "canonical_mainline_reuse",
        "conditional_project_fallback",
        "safe_original_byte_migration",
        "static_evidence_limit",
    },
}
REQUIRED_DISCUSSION_CASES = {
    "discussion-short-grill": {
        "short_grill_artifact_free",
        "static_contract_only",
    },
    "discussion-authorized-checkpoint": {
        "long_grill_supporting_artifact",
        "write_authority_required",
        "material_checkpoint_only",
        "static_contract_only",
    },
    "discussion-unauthorized-candidate": {
        "discussion_checkpoint_candidate",
        "durable_continuity_not_guaranteed",
        "no_canonical_memory_change",
        "static_contract_only",
    },
    "discussion-handoff-playback": {
        "playback_current_route",
        "no_repeated_answered_decision",
        "handoff_continuity",
        "static_contract_only",
    },
    "discussion-replacement-promotion": {
        "replaced_route_superseded",
        "promotion_trigger_and_target",
        "promotion_no_execution_authority",
        "static_contract_only",
    },
}
REQUIRED_SKILL_CASE_CLAUSES = {
    "native-lightweight-control": {"complete_stage_inventory", "native_fast_path"},
    "grill-explicit-skill-invocation": {"explicit_activation", "no_enactment"},
    "grill-negative-signal-control": {"negative_signal_wins", "no_activation"},
    "grill-quoted-marker-control": {"quoted_marker_inert", "no_activation"},
    "grill-question-value-stop": {"mainline_anchoring", "no_implementation_authority"},
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
        "user_facing_changelog",
        "ordinary_user_comprehension",
        "full_version_update_unit",
    },
    "update-user-refresh": {
        "user_refresh_only",
        "source_freshness",
        "profile_preserved",
        "global_install_refresh",
        "project_refresh_when_in_scope",
        "manual_host_actions",
        "readiness_recheck",
        "no_release_metadata",
    },
}
REQUIRED_CASE_TARGET_ROUTES = {
    "update-user-refresh": ("skills/teamwork-update/SKILL.md", "update"),
    "update-release-ledger": ("AGENTS.md", "project-maintainer"),
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
            ("user refresh only", "refresh user installations only"),
            ("profile preserved", "preserve the current install profile"),
            ("global and project refresh", "refresh all global skills, agents, managed policy, routing, and applicable project surfaces"),
            ("readiness recheck", "until it reports `install_ready=yes`"),
            ("no release metadata", "never edit `version`, plugin manifests, changelogs, release commits, tags, or github releases"),
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
    "teamwork-update": {"update-user-refresh"},
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
