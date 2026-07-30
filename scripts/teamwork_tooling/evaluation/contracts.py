"""Schemas and capability coverage for deterministic Teamwork evals."""

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
    "producers",
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
PRODUCER_CLASSES = {
    "root-policy",
    "skill",
    "role-template",
    "artifact-engine",
    "installer",
    "public-contract",
}
PRODUCER_PATH_PREFIXES = {
    "root-policy": ("scripts/install/policy.sh",),
    "skill": ("skills/",),
    "role-template": (
        "templates/codex-agents/",
        "templates/cursor-agents/",
        "templates/claude-agents/",
    ),
    "artifact-engine": ("scripts/", "templates/teamwork-memory/"),
    "installer": ("install.sh", "scripts/install/", "scripts/check-update.sh"),
    "public-contract": (
        "AGENTS.md",
        "README.md",
        "README.en.md",
        "CODEX.md",
        "CURSOR.md",
        "CLAUDE.md",
        "docs/architecture.md",
    ),
}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# The filesystem is the canonical inventory. Validation discovers names from
# skills/*/SKILL.md and protects only the intentionally small public count plus
# named removals; it does not repeat an installer-owned list.
CANONICAL_SKILL_COUNT = 9
RETIRED_SKILLS = {
    "grill-me",
    "teamwork-discuss",
    "teamwork-design",
    "using-teamwork",
    "teamwork-execute",
}

CANONICAL_ROLES = {
    "researcher",
    "explorer",
    "debugger",
    "designer",
    "planner",
    "worker",
    "writer",
    "plan-reviewer",
    "reviewer",
}
ROLE_TEMPLATE_PATHS = {
    "codex": {
        role: f"templates/codex-agents/teamwork-{role}.toml"
        for role in CANONICAL_ROLES
    },
    "cursor": {
        role: f"templates/cursor-agents/{role}.md"
        for role in CANONICAL_ROLES
    },
    "claude": {
        role: f"templates/claude-agents/{role}.md"
        for role in CANONICAL_ROLES
    },
}


def role_sources(role: str) -> set[tuple[str, str]]:
    return {
        ("role-template", ROLE_TEMPLATE_PATHS[host][role])
        for host in PLATFORMS
    }


ROOT_POLICY_SOURCE = {("root-policy", "scripts/install/policy.sh")}
DESIGN_ADVERSARIAL_REFERENCE_PATH = (
    "skills/teamwork-collaborate/references/adversarial-search.md"
)
DESIGN_ADVERSARIAL_REFERENCE_SOURCE = {
    ("skill", DESIGN_ADVERSARIAL_REFERENCE_PATH)
}
COLLABORATE_TRANSACTION_SOURCE = {("artifact-engine", "scripts/discussion-transaction.py")}
INIT_ENGINE_SOURCE = {("artifact-engine", "scripts/init-project-files.py")}
UPDATE_INSTALLER_SOURCE = {("installer", "scripts/check-update.sh")}


CASE_PRODUCER_REQUIREMENTS = {
    ("collaborate", "brainstorm"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("researcher"),
        *role_sources("designer"),
    },
    ("collaborate", "adversarial-challenge"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *DESIGN_ADVERSARIAL_REFERENCE_SOURCE,
        *role_sources("designer"),
    },
    ("research", "external"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-research/SKILL.md"),
        *role_sources("researcher"),
    },
    ("native", "local-evidence"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-explore/SKILL.md"),
        *role_sources("explorer"),
    },
    ("plan", "selected-direction"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-plan/SKILL.md"),
        *role_sources("planner"),
        *role_sources("plan-reviewer"),
    },
    ("collaborate", "dialogue"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("collaborate", "challenge-independent-batch"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("collaborate", "challenge-dependent-sequence"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("collaborate", "explicit-save"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("authority", "permission-boundary"): ROOT_POLICY_SOURCE,
    ("research", "privacy-boundary"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-research/SKILL.md"),
        *role_sources("researcher"),
    },
    ("research", "claim-ledger-conflict"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-research/SKILL.md"),
        *role_sources("researcher"),
        *role_sources("writer"),
    },
    ("research", "lightweight-lookup-control"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-research/SKILL.md"),
        *role_sources("researcher"),
    },
    ("debug", "diagnose-and-fix"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-debug/SKILL.md"),
        *role_sources("debugger"),
    },
    ("goal", "bounded-convergence"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-goal/SKILL.md"),
        *role_sources("worker"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("goal", "failure-evidence-strategy-delta"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-goal/SKILL.md"),
        *role_sources("worker"),
        *role_sources("writer"),
    },
    ("review", "evidence-verdict"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-review/SKILL.md"),
        *role_sources("reviewer"),
    },
    ("review", "unsupported-claim-repair-batch"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-review/SKILL.md"),
        *role_sources("reviewer"),
        *role_sources("writer"),
    },
    ("init", "project-context"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-init/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("worker"),
        *INIT_ENGINE_SOURCE,
    },
    ("init", "exact-root-migration"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-init/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("worker"),
    },
    ("update", "global-refresh"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-update/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("worker"),
        *UPDATE_INSTALLER_SOURCE,
    },
    ("update", "exact-root-migration"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-update/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("worker"),
        *UPDATE_INSTALLER_SOURCE,
    },
    ("ask", "discoverable-native"): ROOT_POLICY_SOURCE,
    ("ask", "required-input"): ROOT_POLICY_SOURCE,
    ("ask", "dialogue-native"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("native", "minimal-change"): {
        *ROOT_POLICY_SOURCE,
        *role_sources("worker"),
    },
    ("native", "engineering-quality"): {
        *ROOT_POLICY_SOURCE,
        *role_sources("worker"),
    },
    ("native", "fanout-context-control"): {
        *ROOT_POLICY_SOURCE,
        *role_sources("worker"),
    },
    ("verification", "monotonic-evidence"): {
        *ROOT_POLICY_SOURCE,
        *role_sources("reviewer"),
    },
    ("platform", "host-boundary"): ROOT_POLICY_SOURCE,
    ("research", "external-boundary"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-research/SKILL.md"),
        *role_sources("researcher"),
        ("skill", "skills/teamwork-explore/SKILL.md"),
        *role_sources("explorer"),
    },
    ("collaborate", "plan-boundary"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        ("skill", "skills/teamwork-plan/SKILL.md"),
        *role_sources("designer"),
        *role_sources("planner"),
        *role_sources("plan-reviewer"),
    },
    ("collaborate", "adversarial-boundary"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *DESIGN_ADVERSARIAL_REFERENCE_SOURCE,
        ("skill", "skills/teamwork-plan/SKILL.md"),
        *role_sources("designer"),
        *role_sources("planner"),
    },
    ("collaborate", "persistence-boundary"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("persistence", "normal-doc-writer"): {
        *role_sources("writer"),
    },
    ("persistence", "generic-artifact-writer"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-plan/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("persistence", "specialized-artifact-writer"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-collaborate/SKILL.md"),
        *role_sources("writer"),
        *COLLABORATE_TRANSACTION_SOURCE,
    },
    ("persistence", "negative-overrides"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-research/SKILL.md"),
        ("skill", "skills/teamwork-plan/SKILL.md"),
        *role_sources("writer"),
    },
    ("persistence", "explore-no-artifact"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-explore/SKILL.md"),
        *role_sources("explorer"),
    },
    ("persistence", "code-coupled-owner"): {
        *ROOT_POLICY_SOURCE,
        *role_sources("worker"),
        *role_sources("writer"),
    },
}

# Coverage is capability based, not case-id based. A case can be renamed or
# rewritten freely as long as the user-visible boundary remains represented.
DEV_CAPABILITY_COVERAGE = {
    ("collaborate", "brainstorm", "en"),
    ("collaborate", "brainstorm", "zh"),
    ("collaborate", "adversarial-challenge", "en"),
    ("collaborate", "adversarial-challenge", "zh"),
    ("research", "external", "en"),
    ("research", "external", "zh"),
    ("native", "local-evidence", "en"),
    ("native", "local-evidence", "zh"),
    ("plan", "selected-direction", "en"),
    ("plan", "selected-direction", "zh"),
    ("collaborate", "dialogue", "en"),
    ("collaborate", "dialogue", "zh"),
    ("collaborate", "challenge-independent-batch", "en"),
    ("collaborate", "challenge-independent-batch", "zh"),
    ("collaborate", "challenge-dependent-sequence", "en"),
    ("collaborate", "challenge-dependent-sequence", "zh"),
    ("collaborate", "explicit-save", "en"),
    ("collaborate", "explicit-save", "zh"),
    ("authority", "permission-boundary", "en"),
    ("research", "privacy-boundary", "en"),
    ("research", "claim-ledger-conflict", "en"),
    ("research", "lightweight-lookup-control", "en"),
    ("debug", "diagnose-and-fix", "en"),
    ("debug", "diagnose-and-fix", "zh"),
    ("goal", "bounded-convergence", "en"),
    ("goal", "bounded-convergence", "zh"),
    ("goal", "failure-evidence-strategy-delta", "en"),
    ("review", "evidence-verdict", "en"),
    ("review", "evidence-verdict", "zh"),
    ("review", "unsupported-claim-repair-batch", "en"),
    ("init", "project-context", "en"),
    ("init", "project-context", "zh"),
    ("init", "exact-root-migration", "en"),
    ("update", "global-refresh", "en"),
    ("update", "global-refresh", "zh"),
    ("update", "exact-root-migration", "en"),
    ("ask", "discoverable-native", "en"),
    ("ask", "discoverable-native", "zh"),
    ("ask", "required-input", "en"),
    ("ask", "required-input", "zh"),
    ("ask", "dialogue-native", "en"),
    ("ask", "dialogue-native", "zh"),
    ("native", "minimal-change", "en"),
    ("native", "minimal-change", "zh"),
    ("native", "engineering-quality", "en"),
    ("native", "fanout-context-control", "en"),
    ("verification", "monotonic-evidence", "en"),
    ("verification", "monotonic-evidence", "zh"),
    ("platform", "host-boundary", "en"),
    ("platform", "host-boundary", "zh"),
    ("persistence", "normal-doc-writer", "en"),
    ("persistence", "generic-artifact-writer", "en"),
    ("persistence", "specialized-artifact-writer", "en"),
    ("persistence", "negative-overrides", "en"),
    ("persistence", "explore-no-artifact", "en"),
    ("persistence", "code-coupled-owner", "en"),
}

RELEASE_CAPABILITY_COVERAGE = {
    ("research", "external-boundary", "en"),
    ("collaborate", "plan-boundary", "en"),
    ("collaborate", "adversarial-boundary", "en"),
    ("collaborate", "persistence-boundary", "en"),
}

CAPABILITY_REQUIREMENTS = {
    ("collaborate", "brainstorm"): {
        "local-constraints-first",
        "evidence-before-strategy-freeze",
        "genuine-tradeoffs-only",
        "recommend-first",
        "default-one-challenge",
        "auto-gate-negative-control",
        "challenge-not-mode",
        "bounded-independent-batch",
        "dependency-serialization",
        "question-criticality",
        "capability-blocked-no-fallback",
        "read-only",
        "no-implementation",
    },
    ("collaborate", "adversarial-challenge"): {
        "input-driven-auto-selection",
        "evidence-before-strategy-freeze",
        "adversarial-not-mode",
        "automatic-default-budget",
        "visible-strategy-reason",
        "dynamic-taxonomy-ledger",
        "two-fresh-critics-per-hypothesis",
        "material-revision-new-trial",
        "two-fresh-final-auditors",
        "dual-pass-required",
        "failure-closed",
        "chat-not-plan-ready",
        "capability-blocked-no-fallback",
        "read-only",
        "no-implementation",
    },
    ("research", "external"): {
        "exact-researcher-dispatch",
        "bounded-sanitized-packet",
        "default-one-child",
        "cap4-daily",
        "five-to-eight-explicit-only",
        "external-sources",
        "current-or-multi-source",
        "citations",
        "fact-inference-separation",
        "claim-map",
        "active-gap",
        "wave-monotonicity",
        "evidence-delta",
        "contradiction-ledger",
        "not-found-ledger",
        "coverage-stop",
        "read-only",
    },
    ("native", "local-evidence"): {
        "local-inspection-native",
        "no-research-activation",
        "no-unnecessary-question",
    },
    ("plan", "selected-direction"): {
        "selected-direction-required",
        "owned-actions",
        "dependencies",
        "open-evidence-dependency",
        "proof-targets",
        "decision-revision",
        "blockers-and-stops",
        "direct-proof",
        "no-redesign",
        "no-implementation",
    },
    ("collaborate", "dialogue"): {
        "natural-activation",
        "sustained-checkpoint",
        "recommend-first",
        "global-decision-map",
        "global-to-detail-order",
        "bounded-independent-batch",
        "one-checkpoint-per-answered-batch",
        "question-criticality",
        "transaction-owned-writer",
        "no-files-overrides",
        "no-implementation",
    },
    ("collaborate", "challenge-independent-batch"): {
        "global-decision-map",
        "global-to-detail-order",
        "bounded-independent-batch",
        "independent-questions",
        "one-checkpoint-per-answered-batch",
        "transaction-owned-writer",
        "recommend-first",
        "question-criticality",
        "closure-signal",
        "no-implementation",
    },
    ("collaborate", "challenge-dependent-sequence"): {
        "global-decision-map",
        "global-to-detail-order",
        "dependency-serialization",
        "one-batch-per-turn",
        "one-checkpoint-per-answered-batch",
        "transaction-owned-writer",
        "recommend-first",
        "question-criticality",
        "closure-signal",
        "no-implementation",
    },
    ("collaborate", "explicit-save"): {
        "explicit-skill-and-save",
        "managed-transaction-only",
        "initialized-writable-project",
        "no-files-overrides",
        "transaction-owned-writer",
        "no-implementation",
    },
    ("authority", "permission-boundary"): {
        "answer-is-not-authority",
        "no-external-effect",
        "no-implementation",
    },
    ("research", "privacy-boundary"): {
        "no-sensitive-query",
        "minimum-disclosure",
        "read-only",
    },
    ("research", "claim-ledger-conflict"): {
        "exact-researcher-dispatch",
        "bounded-sanitized-packet",
        "claim-map",
        "active-gap",
        "wave-monotonicity",
        "evidence-delta",
        "contradiction-ledger",
        "not-found-ledger",
        "coverage-stop",
        "case-v2-artifact-only",
        "no-private-brief-disclosure",
    },
    ("research", "lightweight-lookup-control"): {
        "exact-researcher-dispatch",
        "lookup-depth",
        "one-canonical-source",
        "no-deep-fanout",
        "default-one-child",
        "cap4-daily",
        "five-to-eight-explicit-only",
        "capability-blocked-no-fallback",
    },
    ("debug", "diagnose-and-fix"): {
        "actual-failure-first",
        "frozen-failure-signature",
        "ranked-hypothesis-ledger",
        "hypothesis-before-probes",
        "prediction-falsifier-mapping",
        "one-discriminating-experiment",
        "discriminating-evidence",
        "rejected-hypotheses",
        "authorized-fix-only",
        "same-path-rerun",
        "no-scope-broadening",
        "new-failure-split",
        "no-review-before-cause",
    },
    ("goal", "bounded-convergence"): {
        "explicit-goal",
        "preserve-scope",
        "failure-class",
        "evidence-delta",
        "strategy-delta",
        "status-monotonic",
        "real-success-signal",
        "no-invented-authority",
    },
    ("goal", "failure-evidence-strategy-delta"): {
        "objective",
        "signal",
        "attempt",
        "failure-class",
        "evidence-delta",
        "strategy-delta",
        "status",
        "case-v2-artifact-only",
        "no-narrative-success-upgrade",
    },
    ("review", "evidence-verdict"): {
        "read-only",
        "acceptance-criteria",
        "citation-rich",
        "unsupported-claim",
        "stable-findings",
        "one-repair-batch",
        "one-delta-recheck",
        "evidence-backed-findings",
        "proportional-verification",
        "no-fix",
    },
    ("review", "unsupported-claim-repair-batch"): {
        "sealed-candidate",
        "citation-rich",
        "unsupported-claim",
        "stable-findings",
        "one-repair-batch",
        "one-delta-recheck",
        "case-v2-artifact-only",
        "read-only",
    },
    ("init", "project-context"): {
        "project-only",
        "exact-project-root",
        "migrate-or-resume-only",
        "helper-capability-required",
        "capability-blocked-no-fallback",
        "preserve-human-docs",
        "no-global-refresh",
        "no-external-install",
    },
    ("init", "exact-root-migration"): {
        "exact-project-root",
        "migrate-or-resume-only",
        "helper-capability-required",
        "capability-blocked-no-fallback",
        "case-v2-receipt-only",
        "no-legacy-write-fallback",
    },
    ("update", "global-refresh"): {
        "global-only",
        "exact-project-root",
        "migrate-or-resume-only",
        "helper-capability-required",
        "capability-blocked-no-fallback",
        "preserve-profile",
        "readiness-check",
        "no-project-init",
        "no-release-metadata",
    },
    ("update", "exact-root-migration"): {
        "exact-project-root",
        "migrate-or-resume-only",
        "helper-capability-required",
        "capability-blocked-no-fallback",
        "case-v2-receipt-only",
        "no-project-init-by-default",
    },
    ("ask", "discoverable-native"): {
        "inspect-first",
        "zero-questions",
        "no-collaborate",
        "direct-answer",
    },
    ("ask", "required-input"): {
        "one-required-question",
        "dependent-branch-only",
        "independent-read-only-continues",
        "no-collaborate",
        "no-enactment",
    },
    ("ask", "dialogue-native"): {
        "contribution-first",
        "one-high-information-question",
        "open-or-bounded-native",
        "collaborate-adaptive-mode",
        "no-challenge-premature",
        "semantic-checkpoint",
    },
    ("native", "minimal-change"): {
        "canonical-owner",
        "builtin-or-installed-dependency",
        "minimal-new-logic",
        "native-fast-path",
        "default-one-child",
        "cap4-daily",
        "five-to-eight-explicit-only",
        "host-support-required",
        "bounded-packets",
        "exact-role-matrix",
        "capability-blocked-no-fallback",
        "proportional-proof",
        "no-code-golf",
    },
    ("native", "engineering-quality"): {
        "paired-control",
        "root-and-worker-owner",
        "real-result-first",
        "canonical-reuse",
        "proportional-proof",
        "cohesive-structure",
        "scope-preservation",
        "residue-cleanup",
        "stop-after-proof",
    },
    ("native", "fanout-context-control"): {
        "native-fast-path",
        "default-one-child",
        "cap4-daily",
        "five-to-eight-explicit-only",
        "host-support-required",
        "bounded-packets",
        "exact-role-matrix",
        "capability-blocked-no-fallback",
    },
    ("verification", "monotonic-evidence"): {
        "failed-remains-failed",
        "direct-evidence-only",
        "no-narrative-upgrade",
        "real-path-preferred",
    },
    ("platform", "host-boundary"): {
        "host-tools",
        "host-permissions",
        "no-emulation",
        "semantic-not-mechanical-parity",
    },
    ("research", "external-boundary"): {
        "external-positive",
        "local-negative-control",
        "citations",
        "read-only",
    },
    ("collaborate", "plan-boundary"): {
        "unresolved-options-use-collaborate",
        "selected-direction-uses-plan",
        "no-silent-transition",
        "no-implementation",
    },
    ("collaborate", "adversarial-boundary"): {
        "input-driven-auto-selection",
        "evidence-before-strategy-freeze",
        "weak-cue-negative-control",
        "explicit-strategy-overrides",
        "default-collaborate-stays-lightweight",
        "adversarial-not-mode",
        "chat-not-plan-ready",
        "durable-collaborate-transaction-required",
        "failure-closed",
        "no-silent-transition",
        "no-implementation",
    },
    ("collaborate", "persistence-boundary"): {
        "one-shot-no-write",
        "sustained-checkpoint",
        "challenge-method-for-major-risk",
        "explicit-save-authorizes-transaction",
        "managed-transaction-only",
        "initialized-writable-project",
        "case-v2-artifact-only",
        "no-legacy-write-fallback",
        "no-files-overrides",
        "transaction-owned-writer",
        "no-implementation",
    },
    ("persistence", "normal-doc-writer"): {
        "standalone-doc",
        "bounded-writing-brief",
        "unmanaged-exact-path",
        "no-transaction-required",
        "writer-only",
        "no-research",
        "no-code-coupled-text",
    },
    ("persistence", "generic-artifact-writer"): {
        "default-terminal-workflow-artifacts",
        "terminal-packet-freeze",
        "case-v2-artifact-only",
        "inspect-schema-apply",
        "transaction-derived-destination",
        "ordinary-index-registration",
        "case-bundle-sinks",
        "answer-invariant-overlap-only",
        "writer-join-readback",
        "pre-apply-unsaved-boundary",
        "required-transaction-gate",
        "writer-only",
        "no-implementation-authority",
    },
    ("persistence", "specialized-artifact-writer"): {
        "specialized-collaborate-goal-route",
        "lifecycle-checkpoint-readback",
        "inspect-schema-apply",
        "case-bundle-sinks",
        "transaction-owned-writer",
        "required-transaction-gate",
        "writer-only",
        "no-implementation-authority",
    },
    ("persistence", "negative-overrides"): {
        "no-files-overrides",
        "off-record-overrides",
        "read-only-overrides",
        "no-writes-overrides",
        "deliver-unsaved-result",
        "no-fallback-writer",
    },
    ("persistence", "explore-no-artifact"): {
        "explore-read-only",
        "explore-no-independent-artifact",
        "evidence-belongs-to-consuming-brief",
        "writer-no-independent-explore",
    },
    ("persistence", "code-coupled-owner"): {
        "code-coupled-implementer-owned",
        "writer-forbids-code-comments",
        "writer-forbids-docstrings-tests-schemas",
        "worker-owns-implementation-text",
        "no-writer-fallback",
    },
}

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
NATIVE_QUALITY_PAIR_DIMENSIONS = {
    "canonical-owner",
    "accepted-fallback",
    "proportional-proof",
    "cohesive-structure",
    "scope-residue",
    "result-stop",
}


class EvalError(Exception):
    """Raised when an eval fixture or source contract is invalid."""
