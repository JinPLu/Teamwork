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
CANONICAL_SKILL_COUNT = 10
RETIRED_SKILLS = {"using-teamwork", "teamwork-execute"}

CANONICAL_ROLES = {
    "researcher",
    "explorer",
    "debugger",
    "designer",
    "planner",
    "worker",
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
    "skills/teamwork-design/references/adversarial-search.md"
)
DESIGN_ADVERSARIAL_REFERENCE_SOURCE = {
    ("skill", DESIGN_ADVERSARIAL_REFERENCE_PATH)
}
DISCUSSION_TRANSACTION_SOURCE = {("artifact-engine", "scripts/discussion-transaction.py")}
INIT_ENGINE_SOURCE = {("artifact-engine", "scripts/init-project-files.py")}
UPDATE_INSTALLER_SOURCE = {("installer", "scripts/check-update.sh")}


CASE_PRODUCER_REQUIREMENTS = {
    ("design", "activation"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-design/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("researcher"),
        *role_sources("designer"),
    },
    ("design", "adversarial-activation"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-design/SKILL.md"),
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
    ("grill", "natural-question-first"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/grill-me/SKILL.md"),
    },
    ("grill", "layered-independent-batch"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/grill-me/SKILL.md"),
    },
    ("grill", "layered-dependent-sequence"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/grill-me/SKILL.md"),
    },
    ("grill", "explicit-save"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/grill-me/SKILL.md"),
        *DISCUSSION_TRANSACTION_SOURCE,
    },
    ("authority", "permission-boundary"): ROOT_POLICY_SOURCE,
    ("research", "privacy-boundary"): {
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
        *DISCUSSION_TRANSACTION_SOURCE,
    },
    ("review", "evidence-verdict"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-review/SKILL.md"),
        *role_sources("reviewer"),
    },
    ("init", "project-context"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-init/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("worker"),
        *INIT_ENGINE_SOURCE,
    },
    ("update", "global-refresh"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-update/SKILL.md"),
        *role_sources("explorer"),
        *role_sources("worker"),
        *UPDATE_INSTALLER_SOURCE,
    },
    ("ask", "discoverable-native"): ROOT_POLICY_SOURCE,
    ("ask", "required-input"): ROOT_POLICY_SOURCE,
    ("native", "minimal-change"): {
        *ROOT_POLICY_SOURCE,
        *role_sources("worker"),
    },
    ("native", "engineering-quality"): {
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
    ("design", "design-vs-plan"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-design/SKILL.md"),
        ("skill", "skills/teamwork-plan/SKILL.md"),
        *role_sources("designer"),
        *role_sources("planner"),
        *role_sources("plan-reviewer"),
    },
    ("design", "adversarial-boundary"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/teamwork-design/SKILL.md"),
        *DESIGN_ADVERSARIAL_REFERENCE_SOURCE,
        ("skill", "skills/teamwork-plan/SKILL.md"),
        *role_sources("designer"),
        *role_sources("planner"),
    },
    ("grill", "persistence-boundary"): {
        *ROOT_POLICY_SOURCE,
        ("skill", "skills/grill-me/SKILL.md"),
        *DISCUSSION_TRANSACTION_SOURCE,
    },
}

# Coverage is capability based, not case-id based. A case can be renamed or
# rewritten freely as long as the user-visible boundary remains represented.
DEV_CAPABILITY_COVERAGE = {
    ("design", "activation", "en"),
    ("design", "activation", "zh"),
    ("design", "adversarial-activation", "en"),
    ("design", "adversarial-activation", "zh"),
    ("research", "external", "en"),
    ("research", "external", "zh"),
    ("native", "local-evidence", "en"),
    ("native", "local-evidence", "zh"),
    ("plan", "selected-direction", "en"),
    ("plan", "selected-direction", "zh"),
    ("grill", "natural-question-first", "en"),
    ("grill", "natural-question-first", "zh"),
    ("grill", "layered-independent-batch", "en"),
    ("grill", "layered-independent-batch", "zh"),
    ("grill", "layered-dependent-sequence", "en"),
    ("grill", "layered-dependent-sequence", "zh"),
    ("grill", "explicit-save", "en"),
    ("grill", "explicit-save", "zh"),
    ("authority", "permission-boundary", "en"),
    ("research", "privacy-boundary", "en"),
    ("debug", "diagnose-and-fix", "en"),
    ("debug", "diagnose-and-fix", "zh"),
    ("goal", "bounded-convergence", "en"),
    ("goal", "bounded-convergence", "zh"),
    ("review", "evidence-verdict", "en"),
    ("review", "evidence-verdict", "zh"),
    ("init", "project-context", "en"),
    ("init", "project-context", "zh"),
    ("update", "global-refresh", "en"),
    ("update", "global-refresh", "zh"),
    ("ask", "discoverable-native", "en"),
    ("ask", "discoverable-native", "zh"),
    ("ask", "required-input", "en"),
    ("ask", "required-input", "zh"),
    ("native", "minimal-change", "en"),
    ("native", "minimal-change", "zh"),
    ("native", "engineering-quality", "en"),
    ("verification", "monotonic-evidence", "en"),
    ("verification", "monotonic-evidence", "zh"),
    ("platform", "host-boundary", "en"),
    ("platform", "host-boundary", "zh"),
}

RELEASE_CAPABILITY_COVERAGE = {
    ("research", "external-boundary", "en"),
    ("design", "design-vs-plan", "en"),
    ("design", "adversarial-boundary", "en"),
    ("grill", "persistence-boundary", "en"),
}

CAPABILITY_REQUIREMENTS = {
    ("design", "activation"): {
        "local-constraints-first",
        "evidence-before-strategy-freeze",
        "genuine-tradeoffs-only",
        "recommend-first",
        "default-one-challenge",
        "auto-gate-negative-control",
        "bounded-independent-batch",
        "dependency-serialization",
        "question-criticality",
        "read-only",
        "no-implementation",
    },
    ("design", "adversarial-activation"): {
        "input-driven-auto-selection",
        "evidence-before-strategy-freeze",
        "automatic-default-budget",
        "visible-strategy-reason",
        "dynamic-taxonomy-ledger",
        "two-fresh-critics-per-hypothesis",
        "material-revision-new-trial",
        "two-fresh-final-auditors",
        "dual-pass-required",
        "failure-closed",
        "chat-not-plan-ready",
        "read-only",
        "no-implementation",
    },
    ("research", "external"): {
        "external-sources",
        "current-or-multi-source",
        "citations",
        "fact-inference-separation",
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
        "direct-proof",
        "no-redesign",
        "no-implementation",
    },
    ("grill", "natural-question-first"): {
        "natural-activation",
        "ordinary-no-write",
        "major-change-auto-transaction",
        "recommend-first",
        "global-decision-map",
        "bounded-independent-batch",
        "question-criticality",
        "transaction-owned-writer",
        "no-files-overrides",
        "no-implementation",
    },
    ("grill", "layered-independent-batch"): {
        "global-decision-map",
        "bounded-independent-batch",
        "independent-questions",
        "recommend-first",
        "question-criticality",
        "closure-signal",
        "no-implementation",
    },
    ("grill", "layered-dependent-sequence"): {
        "global-decision-map",
        "dependency-serialization",
        "one-batch-per-turn",
        "recommend-first",
        "question-criticality",
        "closure-signal",
        "no-implementation",
    },
    ("grill", "explicit-save"): {
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
    ("debug", "diagnose-and-fix"): {
        "actual-failure-first",
        "discriminating-evidence",
        "authorized-fix-only",
        "same-path-rerun",
        "no-scope-broadening",
    },
    ("goal", "bounded-convergence"): {
        "explicit-goal",
        "preserve-scope",
        "strategy-delta",
        "real-success-signal",
        "no-invented-authority",
    },
    ("review", "evidence-verdict"): {
        "read-only",
        "acceptance-criteria",
        "evidence-backed-findings",
        "proportional-verification",
        "no-fix",
    },
    ("init", "project-context"): {
        "project-only",
        "preserve-human-docs",
        "no-global-refresh",
        "no-external-install",
    },
    ("update", "global-refresh"): {
        "global-only",
        "preserve-profile",
        "readiness-check",
        "no-project-init",
        "no-release-metadata",
    },
    ("ask", "discoverable-native"): {
        "inspect-first",
        "zero-questions",
        "no-grill",
        "direct-answer",
    },
    ("ask", "required-input"): {
        "one-required-question",
        "dependent-branch-only",
        "independent-read-only-continues",
        "no-grill",
        "no-enactment",
    },
    ("native", "minimal-change"): {
        "canonical-owner",
        "builtin-or-installed-dependency",
        "minimal-new-logic",
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
    ("design", "design-vs-plan"): {
        "unresolved-options-use-design",
        "selected-direction-uses-plan",
        "no-silent-transition",
        "no-implementation",
    },
    ("design", "adversarial-boundary"): {
        "input-driven-auto-selection",
        "evidence-before-strategy-freeze",
        "weak-cue-negative-control",
        "explicit-strategy-overrides",
        "default-design-stays-lightweight",
        "chat-not-plan-ready",
        "durable-design-transaction-required",
        "failure-closed",
        "no-silent-transition",
        "no-implementation",
    },
    ("grill", "persistence-boundary"): {
        "ordinary-no-write",
        "major-change-auto-transaction",
        "explicit-save-authorizes-transaction",
        "managed-transaction-only",
        "initialized-writable-project",
        "no-files-overrides",
        "transaction-owned-writer",
        "no-implementation",
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
