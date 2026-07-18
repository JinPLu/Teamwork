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
        "mainline_anchoring",
        "public_decision_retained",
        "implementation_detail_deprioritized",
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
    "plan-ask-readiness": {
        "plan_uses_shared_ask_gate",
        "plan_complexity_not_grill",
        "brief_decision_checkpoint",
        "settled_and_open_visible",
        "no_execution_authority",
    },
    "review-bounded-recheck": {"stable_finding_ids", "review_taxonomy", "blocker_classification", "one_corrective_recheck"},
    "goal-dependent-branch-retry": {"current_blocker_only", "independent_work_continues", "native_goal_authority"},
    "ask-confirmation-authority": {"plan_acceptance_only", "no_implementation_authority", "no_release_authority"},
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
        "real_result_first",
        "stop_after_result",
    },
    "minimality-justified-surface": {
        "accepted_behavior_justifies_new_logic",
        "justified_abstraction_or_dependency",
        "multi_file_allowed",
        "proportional_proof",
        "real_result_first",
        "stop_after_result",
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
        "short_grill_no_write",
        "static_contract_only",
    },
    "discussion-authorized-checkpoint": {
        "observable_discussion_trigger",
        "explicit_grill_narrow_discussion_authority",
        "supporting_artifact_only",
        "five_section_human_recovery",
        "persistence_before_next_question",
        "readback_verified_anchors",
        "static_contract_only",
    },
    "discussion-explicit-save-only": {
        "explicit_save_or_resume_trigger",
        "explicit_grill_narrow_discussion_authority",
        "independent_usefulness_trigger",
        "static_contract_only",
    },
    "discussion-handoff-only": {
        "handoff_or_compaction_trigger",
        "explicit_grill_narrow_discussion_authority",
        "independent_usefulness_trigger",
        "static_contract_only",
    },
    "discussion-three-branch-only": {
        "three_real_branches_trigger",
        "explicit_grill_narrow_discussion_authority",
        "independent_usefulness_trigger",
        "static_contract_only",
    },
    "discussion-short-explicit-save": {
        "explicit_save_or_resume_trigger",
        "explicit_grill_narrow_discussion_authority",
        "shortness_not_a_veto",
        "static_contract_only",
    },
    "discussion-single-conclusion-continuity": {
        "single_conclusion_open_discriminator_trigger",
        "no_second_settled_choice_threshold",
        "persistence_before_next_question",
        "same_turn_persistence_no_status_deferral",
        "five_section_human_recovery",
        "static_contract_only",
    },
    "discussion-resume-no-new-input": {
        "inspect_canonical_state",
        "resume_without_new_input_is_read_only",
        "no_schema_or_apply",
        "ask_saved_unresolved_question",
        "static_contract_only",
    },
    "discussion-unauthorized-candidate": {
        "discussion_checkpoint_candidate",
        "ordinary_plan_no_grill",
        "durable_continuity_not_guaranteed",
        "no_canonical_memory_change",
        "no_write_authority",
        "static_contract_only",
    },
    "discussion-handoff-recovery": {
        "human_recoverability",
        "five_section_recovery",
        "no_repeated_answered_decision",
        "handoff_continuity",
        "static_contract_only",
    },
    "discussion-human-recovery": {
        "specific_topic_h1",
        "five_section_recovery",
        "decision_map_optional_for_three_branches",
        "human_recoverability",
        "static_contract_only",
    },
    "discussion-replacement-promotion": {
        "replaced_discussion_superseded",
        "promotion_trigger_and_target",
        "promotion_no_execution_authority",
        "static_contract_only",
    },
}
REQUIRED_AUDIENCE_CASES = {
    "audience-first-community-research": {
        "audience_first_answer",
        "plain_causal_explanation",
        "relevance_gate",
        "no_irrelevant_internal_detail",
        "no_generic_proof_status",
        "specific_material_uncertainty",
        "decision_appropriate_next_step",
        "static_contract_only",
    },
    "audience-skill-explanation-contrast": {
        "skill_explanation_allowed",
        "capability_or_limit_relevance",
        "engineering_process_dump_rejected",
        "static_contract_only",
    },
    "audience-one-sentence-fact-control": {
        "shortest_complete_answer",
        "one_sentence_control",
        "no_forced_cause",
        "no_forced_action",
        "static_contract_only",
    },
    "audience-reader-argument": {
        "connected_reader_argument",
        "observation_inference_separation",
        "term_stability",
        "decision_boundary",
        "no_stock_proof_status",
        "static_contract_only",
    },
    "audience-continuing-mainline": {
        "discussion_mainline",
        "mainline_advanced",
        "status_displacement_rejected",
        "term_stability",
        "static_contract_only",
    },
}
REQUIRED_HANDOFF_CASES = {
    "subagent-minimal-handoff": {
        "conclusion",
        "direct_evidence",
        "unresolved_impact",
        "next_action",
        "root_translation",
        "static_contract_only",
    },
}
REQUIRED_RULE_MAINTENANCE_CASES = {
    "rule-maintenance-audit": {
        "canonical_owner",
        "user_effect",
        "narrow_changed_rule_check",
        "no_validation_ceremony",
        "static_contract_only",
    },
}
REQUIRED_ACTIVATION_CASES = {
    "activation-native-en": ("en", "native", "skills/using-teamwork/SKILL.md", "direct_action"),
    "activation-native-zh": ("zh", "native", "skills/using-teamwork/SKILL.md", "direct_action"),
    "activation-router-en": ("en", "router", "skills/using-teamwork/SKILL.md", "ordered_stages"),
    "activation-router-zh": ("zh", "router", "skills/using-teamwork/SKILL.md", "ordered_stages"),
    "activation-research-en": ("en", "research", "skills/teamwork-research/SKILL.md", "source_grounded_answer"),
    "activation-research-zh": ("zh", "research", "skills/teamwork-research/SKILL.md", "source_grounded_answer"),
    "activation-debug-en": ("en", "debug", "skills/teamwork-debug/SKILL.md", "repro_before_fix"),
    "activation-debug-zh": ("zh", "debug", "skills/teamwork-debug/SKILL.md", "repro_before_fix"),
    "activation-plan-en": ("en", "plan", "skills/teamwork-plan/SKILL.md", "decision_ready_no_write"),
    "activation-plan-zh": ("zh", "plan", "skills/teamwork-plan/SKILL.md", "decision_ready_no_write"),
    "activation-grill-en": ("en", "grill", "skills/grill-me/SKILL.md", "native_question_no_write"),
    "activation-grill-zh": ("zh", "grill", "skills/grill-me/SKILL.md", "native_question_no_write"),
    "activation-execute-en": ("en", "execute", "skills/teamwork-execute/SKILL.md", "scoped_change_and_checks"),
    "activation-execute-zh": ("zh", "execute", "skills/teamwork-execute/SKILL.md", "scoped_change_and_checks"),
    "activation-review-en": ("en", "review", "skills/teamwork-review/SKILL.md", "evidence_backed_verdict"),
    "activation-review-zh": ("zh", "review", "skills/teamwork-review/SKILL.md", "evidence_backed_verdict"),
    "activation-goal-en": ("en", "goal", "skills/teamwork-goal/SKILL.md", "bounded_convergence"),
    "activation-goal-zh": ("zh", "goal", "skills/teamwork-goal/SKILL.md", "bounded_convergence"),
    "activation-init-en": ("en", "init", "skills/teamwork-init/SKILL.md", "project_context_setup"),
    "activation-init-zh": ("zh", "init", "skills/teamwork-init/SKILL.md", "project_context_setup"),
    "activation-update-en": ("en", "update", "skills/teamwork-update/SKILL.md", "global_refresh"),
    "activation-update-zh": ("zh", "update", "skills/teamwork-update/SKILL.md", "global_refresh"),
}
REQUIRED_ACTIVATION_COVERAGE = {
    "weak_cue",
    "observable_contract",
    "static_contract_only",
}
ACTIVATION_PROMPT_STAGE_RE = re.compile(
    r"(?i)(?:\b(?:native|router|research|debug|plan|grill|execute|review|goal|init|update)\b|"
    r"\b(?:using-teamwork|grill-me|teamwork-[a-z-]+)\b|"
    r"(?:研究阶段|调试阶段|计划阶段|规划阶段|执行阶段|评审阶段|审查阶段|目标模式|初始化阶段|更新阶段))"
)
REQUIRED_SKILL_CASE_CLAUSES = {
    "native-lightweight-control": {"native_fast_path", "real_result_first", "stop_after_result"},
    "grill-explicit-skill-invocation": {"explicit_activation", "no_enactment"},
    "grill-negative-signal-control": {"negative_signal_wins", "no_activation"},
    "grill-quoted-marker-control": {"quoted_marker_inert", "no_activation"},
    "grill-question-value-stop": {
        "mainline_anchoring",
        "public_decision_retained",
        "implementation_detail_deprioritized",
        "no_implementation_authority",
    },
    "research-source-quality": {"observed_inferred_claimed", "read_only_boundary"},
    "debug-repro-before-fix": {
        "first_blocking_error",
        "discriminating_evidence",
        "same_path_rerun",
        "no_broad_investigation",
    },
    "plan-ask-readiness": {
        "plan_uses_shared_ask_gate",
        "plan_complexity_not_grill",
        "brief_decision_checkpoint",
        "settled_and_open_visible",
        "no_execution_authority",
    },
    "complex-coding-discipline": {
        "real_result_first",
        "named_boundary_only",
        "discovery_classification",
        "stop_after_result",
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
        "current_blocker_only",
        "real_success_signal",
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
        "project_init_separate",
        "manual_host_actions",
        "managed_readiness",
        "host_activation_readiness",
        "single_active_skill",
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
            (
                "Native fast path",
                "authorized change/build work stays native or goes straight to execute",
            ),
            (
                "known-facts native explanation",
                "when all decision-relevant facts are supplied, a stable explanation stays native",
            ),
            (
                "supplied-facts concise explanation",
                "for a supplied-facts explanation, name the conclusion and missing discriminator once, then stop",
            ),
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
            ("explicit activation", "enter only for a user-originated challenge or question-first request"),
            (
                "frontmatter natural explicit entry",
                "description: Use when the user asks to be challenged, grilled, or questioned before action",
            ),
            ("Plan complexity stays out", "plan complexity, artifact usefulness, and ordinary clarification do not activate grill"),
            ("negative intent wins", "explicit negative intent wins"),
            ("inert mentions", "quoted, file, tool, example, or maintenance mentions are inert"),
            (
                "evidence-backed recommended answer",
                "before each question, inspect discoverable evidence and give grounded recommendation",
            ),
            (
                "concise text fallback",
                "host's native interaction surface if callable, else one concise text question",
            ),
            ("no execution authority", "confirmation does not grant implementation authority"),
        ),
    ),
    "teamwork-research": (
        "skills/teamwork-research/SKILL.md",
        (
            ("natural research intent", "description: Use when the user needs facts checked before action"),
            ("observed/inferred/claimed evidence", "`observed`, `inferred`, and `claimed` findings"),
            ("read-only boundary", "research does not authorize edits, external writes"),
            (
                "supplied-facts native boundary",
                "do not enter merely to explain supplied facts when no lookup or stale-assumption check is needed; return to native",
            ),
        ),
    ),
    "teamwork-debug": (
        "skills/teamwork-debug/SKILL.md",
        (
            ("unknown-cause debug intent", "description: Use when a failure, crash, flake, regression, or unexpected result has an unknown cause"),
            ("real failure first", "start from the actual failing command, environment, and first blocking error"),
            ("discriminating evidence only", "gather only evidence that distinguishes the next possible fix"),
            ("same-path rerun", "rerun the same real path"),
        ),
    ),
    "teamwork-plan": (
        "skills/teamwork-plan/SKILL.md",
        (
            ("Plan complexity does not activate Grill", "plan complexity never activates `grill-me`"),
            ("shared Ask Gate", "apply the shared ask gate and ask only that question"),
            ("clear work executes", "clear authorized work executes without first manufacturing a plan"),
            ("resolved choices captured in the plan", "summarize them in the plan"),
            (
                "brief Settled/Still open checkpoint",
                "`settled: ...` / `still open: ...` checkpoint",
            ),
            ("no execution authority", "confirmation grants no implementation, release, external-effect, or other authority"),
        ),
    ),
    "teamwork-execute": (
        "skills/teamwork-execute/SKILL.md",
        (
            ("natural execute intent", "description: Use when the user asks to implement, build, change, fix, or continue scoped work"),
            ("plan optional", "a plan is optional"),
            ("real path first", "reach the shortest safe real run or artifact as early as possible"),
            ("discovery classification", "classify discoveries:"),
            ("proxy checks cannot replace delivery", "never substitute plan/mock/static success for an available real path"),
            ("stop after result", "with no unchecked named boundary, stop"),
        ),
    ),
    "teamwork-review": (
        "skills/teamwork-review/SKILL.md",
        (
            ("natural review intent", "description: Use when the user asks whether work is correct or complete"),
            ("review taxonomy must be BLOCKER, FOLLOW-UP, or SUGGESTION", "one class: `blocker`, `follow-up`, or `suggestion`"),
            ("no completion review ceremony", "do not start an independent review merely because implementation finished"),
            ("risk-gated fresh review", "public/shared contracts, release, destructive action, or security/permission/data boundaries"),
            ("one bounded recheck", "permit one corrective recheck"),
        ),
    ),
    "teamwork-goal": (
        "skills/teamwork-goal/SKILL.md",
        (
            ("natural goal intent", "description: Use when the user asks Codex to keep working until a verifiable result"),
            ("explicit user request or accepted Goal Proposal", "only when the user explicitly requests goal mode or accepts a goal proposal"),
            ("preserved Goal Invariants", "identify the preserved scope/invariants, failed claim and stage, prior evidence, do-not-repeat constraints"),
            ("strategy delta", "stop on repeated no-progress without an evidence-backed strategy delta"),
            ("current blocker only", "route only the current blocker"),
            ("real success signal", "mark complete when the real success signal passes"),
        ),
    ),
    "teamwork-init": (
        "skills/teamwork-init/SKILL.md",
        (
            ("natural init intent", "description: Use when a project needs agent instructions or Teamwork context set up"),
            ("readiness gaps", "reported gaps, not stop conditions"),
            (
                "safe project-context continuation",
                "project instructions, memory, and codegraph context can continue when the global install returns an actionable configuration failure",
            ),
            ("host-owned tools", "native interaction tools are host capabilities, not teamwork installation requirements"),
            ("external tooling approval", "do not install external tooling without approval"),
        ),
    ),
    "teamwork-update": (
        "skills/teamwork-update/SKILL.md",
        (
            ("natural update intent", "description: Use when the user asks to check or refresh globally installed Teamwork skills"),
            (
                "global user refresh only",
                "refresh global user installations only",
            ),
            ("profile preserved", "preserve the current install profile"),
            (
                "global refresh",
                "for a global-only refresh of skills, agents, managed policy, and routing",
            ),
            (
                "project initialization ownership",
                "project initialization and project-context changes belong to `teamwork-init`",
            ),
            ("managed readiness", "`managed_install_ready=yes` proves managed files are current"),
            ("host activation readiness", "it is not full host activation when `host_activation=manual-action-required`"),
            ("execute refresh", "do not stop at command advice while the command remains safe and in scope"),
            ("single active catalog entry", "verify each teamwork skill appears once"),
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
