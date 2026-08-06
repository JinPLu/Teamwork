"""Small contracts for Teamwork structural and behavioral evaluations."""

from __future__ import annotations

import os
import re
from pathlib import Path

from teamwork_tooling.topology import agent_template_paths, host_role_paths, public_skill_paths


ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = ROOT / "evals" / "teamwork"
ROUTING_MANIFEST = EVAL_ROOT / "routing-pairs.json"
RUBRIC_DIR = EVAL_ROOT / "rubrics"
OUTPUT_DIR = Path(os.environ.get("TEAMWORK_EVAL_OUTPUT_DIR", EVAL_ROOT / "outputs"))
SPLITS = {"dev", "release"}
PLATFORMS = {"codex", "cursor", "claude"}
SEMANTIC_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PUBLIC_SKILL_PATHS = public_skill_paths(ROOT)
CANONICAL_ROLES = frozenset(agent_template_paths(ROOT))
ROLE_TEMPLATE_PATHS = host_role_paths(ROOT)


class EvalError(Exception):
    """Raised when an evaluation fixture or source contract is invalid."""
