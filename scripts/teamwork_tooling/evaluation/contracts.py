"""Small, manifest-driven contracts for deterministic Teamwork evaluations."""

from __future__ import annotations

import os
import re
from pathlib import Path

from teamwork_tooling.topology import agent_template_paths, host_role_paths, public_skill_paths


ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = ROOT / "evals" / "teamwork"
PAIR_MANIFEST = EVAL_ROOT / "routing-pairs.json"
RUBRIC_DIR = EVAL_ROOT / "rubrics"
OUTPUT_DIR = Path(os.environ.get("TEAMWORK_EVAL_OUTPUT_DIR", EVAL_ROOT / "outputs"))

SPLITS = {"dev", "release"}
PLATFORMS = {"codex", "cursor", "claude"}
PAIR_POLARITIES = {"positive", "negative"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

PUBLIC_SKILL_PATHS = public_skill_paths(ROOT)
CANONICAL_ROLES = frozenset(agent_template_paths(ROOT))
ROLE_TEMPLATE_PATHS = host_role_paths(ROOT)

LEDGER_SCHEMAS = {
    "optimizer-candidates.jsonl": {
        "date", "candidate_id", "kind", "provider", "model", "model_config",
        "prompt_or_template", "owned_files", "denylist", "baseline", "treatment",
        "gate_decision", "rollback", "validation", "release_audit", "reviewer", "decision",
    },
}
OPTIMIZER_KINDS = {"skillopt-lite", "harnessopt-lite"}
OPTIMIZER_GATE_DECISIONS = {"accept_new_best", "accept", "reject", "flat", "blocked"}
OPTIMIZER_DECISIONS = {"candidate", "accepted", "rejected", "blocked"}
PLACEHOLDER = "not_applicable"


class EvalError(Exception):
    """Raised when an eval fixture or source contract is invalid."""
