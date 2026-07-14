"""Validation of Teamwork source contracts."""

from __future__ import annotations

import re

from .contracts import EvalError, ROOT, SKILL_SOURCE_CONTRACTS


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


def _require_source_clauses(
    path: str, text: str, family: str, clauses: tuple[tuple[str, str], ...]
) -> None:
    normalized = normalize_semantic_text(text)
    for label, clause in clauses:
        if normalize_semantic_text(clause) not in normalized:
            raise EvalError(f"{path}: {family} must preserve {label}")


def validate_always_loaded_policy_text(policy_text: str) -> None:
    """Keep the compact policy behavior-bearing rather than deletion-optimized."""

    path = "scripts/install/policy.sh"
    _require_source_clauses(
        path,
        policy_text,
        "always-loaded policy",
        (
            ("request scope", "work within the user's request"),
            (
                "root translation",
                "the root owns user questions and translates results",
            ),
            (
                "read-only stage boundary",
                "research/debug/plan/review are read-only absent change authority",
            ),
            (
                "research and debug routing",
                "route unknown facts/options/repro to research; unknown-cause failures to debug",
            ),
            (
                "explicit Grill boundary",
                "grill only for explicit requests or material non-simple plans",
            ),
            (
                "inert marker boundary",
                "negative/quoted/file/tool/example/maintenance text is inert",
            ),
            (
                "audience-first reply",
                "default user-facing replies: lead with conclusion, why it matters, causal explanation, and useful action when relevant",
            ),
            (
                "relevance gate",
                "omit versions, unexplained/self-invented labels, process narration, and repeated generic caveats unless requested or material",
            ),
            (
                "specific material uncertainty",
                "state material uncertainty once: unknown, impact, and needed evidence",
            ),
        ),
    )
    for writer in (
        "write_teamwork_codex_global_policy",
        "write_teamwork_cursor_global_policy",
        "write_teamwork_claude_global_policy",
    ):
        match = re.search(
            rf"(?ms)^{re.escape(writer)}\(\) \{{(.*?)^\}}", policy_text
        )
        if not match or "write_teamwork_global_policy_body" not in match.group(1):
            raise EvalError(
                f"{path}: always-loaded policy must be shared by {writer}"
            )


def validate_audience_source_text(workflow_contract_text: str) -> None:
    _require_source_clauses(
        "skills/using-teamwork/references/workflow-contract.md",
        workflow_contract_text,
        "audience-first contract",
        (
            (
                "audience-first conclusion",
                "default to audience-first replies: lead with the conclusion and why it matters",
            ),
            ("plain causal explanation", "the shortest plain causal explanation"),
            ("relevance gate", "use a relevance gate"),
            (
                "irrelevant-detail omission",
                "omit versions, unexplained or self-invented labels, engineering/process narration",
            ),
            (
                "specific material uncertainty",
                "state material uncertainty once: what is unknown, why it matters, and the evidence or action that would resolve it",
            ),
            ("no false certainty", "never turn uncertainty into certainty"),
        ),
    )


def validate_rule_maintenance_source_text(workflow_contract_text: str) -> None:
    _require_source_clauses(
        "skills/using-teamwork/references/workflow-contract.md",
        workflow_contract_text,
        "rule-maintenance audit",
        (
            (
                "canonical owner, user effect, and verification",
                "audit the canonical owner, user effect, and verification",
            ),
            ("plain-language result", "explain the result in plain language"),
        ),
    )


def validate_decision_checkpoint_source_text(
    workflow_contract_text: str, plan_text: str, plan_output_text: str
) -> None:
    sources = {
        "skills/using-teamwork/references/workflow-contract.md": workflow_contract_text,
        "skills/teamwork-plan/SKILL.md": plan_text,
        "skills/using-teamwork/references/plan-output.md": plan_output_text,
    }
    for path, text in sources.items():
        _require_source_clauses(
            path,
            text,
            "brief decision checkpoint",
            (
                ("Settled field", "settled:"),
                ("Still open field", "still open:"),
                ("human-readable boundary", "human-readable"),
                ("no authority grant", "authority"),
            ),
        )


def validate_minimal_handoff_source_text(
    subagent_contract_text: str, subagent_dispatch_text: str
) -> None:
    _require_source_clauses(
        "skills/using-teamwork/references/subagent-contract.md",
        subagent_contract_text,
        "minimal subagent handoff",
        (
            ("Conclusion", "conclusion:"),
            ("Direct Evidence", "direct evidence:"),
            ("Unresolved Impact", "unresolved impact:"),
            ("Next Action", "next action:"),
            (
                "root translation",
                "root translates it into an audience-first response for people",
            ),
        ),
    )
    _require_source_clauses(
        "skills/using-teamwork/references/subagent-dispatch.md",
        subagent_dispatch_text,
        "minimal subagent handoff",
        (
            (
                "four-field return",
                "conclusion, direct evidence, unresolved impact, and next action",
            ),
            ("root translation", "root translates internal results into an audience-first response"),
        ),
    )


def discussion_section(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text
    )
    if not match:
        raise EvalError(
            "skills/using-teamwork/references/teamwork-discussion-template.md: "
            f"missing {heading} section"
        )
    return match.group(1).strip()


def validate_discussion_template_text(template_text: str) -> None:
    path = "skills/using-teamwork/references/teamwork-discussion-template.md"
    if not re.search(r"(?m)^Artifact Type: discussion\s*$", template_text):
        raise EvalError(f"{path}: header must declare Artifact Type: discussion")
    if not re.search(r"(?m)^Authority: supporting\s*$", template_text):
        raise EvalError(f"{path}: header must declare Authority: supporting")

    starting_question = discussion_section(template_text, "Starting Question")
    for field in ("Mainline or project goal", "Decision", "Why now"):
        if not re.search(rf"(?mi)^- {re.escape(field)}:\s*\S", starting_question):
            raise EvalError(f"{path}: Starting Question must include {field}")

    decision_state = discussion_section(template_text, "Decision State")
    for field in ("Decisions", "Open", "Rejected", "Evidence", "Resume point", "Promotion"):
        if not re.search(rf"(?mi)^- {re.escape(field)}:\s*\S", decision_state):
            raise EvalError(f"{path}: Decision State must include {field}")

    route_map = discussion_section(template_text, "Route Map")
    mermaid = re.search(r"(?ms)```mermaid\s*\n(.*?)```", route_map)
    if not mermaid or not re.search(r"(?m)^\s*flowchart\b", mermaid.group(1)):
        raise EvalError(f"{path}: Route Map must contain a Mermaid flowchart")
    diagram = mermaid.group(1)
    nodes = re.findall(r'(?m)^\s*(R[1-9][0-9]*)\s*\["([^"]+)"\]\s*$', diagram)
    if not nodes:
        raise EvalError(f"{path}: Route Map must define artifact-local R<number> nodes")
    map_keys = [key for key, _ in nodes]
    if len(map_keys) != len(set(map_keys)):
        raise EvalError(f"{path}: Route Map node keys must be unique")
    undefined = sorted(
        {
            key
            for edge in re.findall(
                r"(?m)^\s*(R[1-9][0-9]*)\s*-->\s*(R[1-9][0-9]*)\s*$",
                diagram,
            )
            for key in edge
            if key not in set(map_keys)
        }
    )
    if undefined:
        raise EvalError(
            f"{path}: Route Map edges reference undefined node keys: "
            + ", ".join(undefined)
        )
    for key, label in nodes:
        if not normalize_semantic_text(label).startswith(key.casefold() + " "):
            raise EvalError(f"{path}: diagram node {key} must include its artifact-local key")
        if re.search(r"(?i)\b(?:evidence|outcome|reason|mainline impact)\s*:", label):
            raise EvalError(f"{path}: Route Map must not duplicate Decision State details")

    playback = discussion_section(template_text, "Textual Playback")
    if "```" in playback or re.search(r"(?m)^\s*\|.*\|\s*$", playback):
        raise EvalError(f"{path}: Textual Playback must be plain text")
    normalized_playback = normalize_semantic_text(playback)
    for anchor in (
        "starting question",
        "evidence or decision",
        "settled/open/rejected state",
        "exact point at which to resume",
        "do not reproduce dialogue or a raw transcript",
    ):
        if normalize_semantic_text(anchor) not in normalized_playback:
            raise EvalError(f"{path}: Textual Playback must preserve {anchor}")

    update_rules = discussion_section(template_text, "Update Rules")
    normalized_rules = normalize_semantic_text(update_rules)
    for label, anchor in (
        ("material-checkpoint updates", "update only at a material checkpoint"),
        ("no per-turn writes", "do not update per turn"),
        ("privacy-safe summaries", "privacy-safe summaries only"),
        ("no transcripts or hidden reasoning", "exclude raw transcripts, hidden reasoning, secrets, and unnecessary personal data"),
        ("promotion authority boundary", "promotion does not grant execution authority"),
    ):
        if normalize_semantic_text(anchor) not in normalized_rules:
            raise EvalError(f"{path}: Update Rules must preserve {label}")


def validate_discussion_source_text(
    grill_text: str,
    router_text: str,
    artifact_protocol_text: str,
    template_text: str,
) -> None:
    path = "skills/using-teamwork/references/artifact-protocol.md"
    combined = "\n".join((grill_text, router_text, artifact_protocol_text, template_text))
    if "docs/teamwork/discussions/" in combined:
        raise EvalError(f"{path}: use the singular discussion path")
    if "`docs/teamwork/discussion/YYYY-MM-DD-<slug>.md`" not in artifact_protocol_text:
        raise EvalError(f"{path}: preserve the singular discussion path")

    source_contracts = (
        (
            "skills/grill-me/SKILL.md",
            grill_text,
            (
                ("short Grill artifact-free", "keep short grill artifact-free"),
                ("long Grill trigger", "for a long, cross-context, handoff-sensitive, or materially branching grill"),
                ("supporting memory", "it is supporting memory, not a transcript or execution authority"),
                ("material checkpoints", "updated only at material checkpoints"),
                ("unauthorized candidate", "without write authority, return a **discussion checkpoint candidate**"),
                ("continuity warning", "durable continuity is not guaranteed"),
                ("answered-decision recovery", "do not invent choices, fill a quota, or repeat an answered decision"),
            ),
        ),
        (
            "skills/using-teamwork/SKILL.md",
            router_text,
            (("task replacement termination", "task replacement ends it"),),
        ),
        (
            path,
            artifact_protocol_text,
            (
                ("supporting-only boundary", "it is not a transcript, a new skill, stage, route, mode, state machine, or source of execution authority"),
                ("supporting authority header", "every persisted discussion has `authority: supporting`"),
                ("canonical and execution authority boundary", "stays subordinate to canonical project sources. it cannot promote itself or authorize execution"),
                ("write authority", "creation and updates require write authority"),
                ("candidate continuity warning", "without it, return a **discussion checkpoint candidate** in chat and state that durable continuity is not guaranteed"),
                ("material-checkpoint updates", "do not update per turn"),
                (
                    "required route map and textual playback",
                    "every persisted discussion includes both a full route map and a textual playback",
                ),
                (
                    "privacy boundary",
                    "keep only privacy-safe summaries; never store hidden reasoning, secrets, or unnecessary personal data",
                ),
                ("promotion authority boundary", "does not grant execution authority"),
            ),
        ),
    )
    for source_path, text, clauses in source_contracts:
        normalized = normalize_semantic_text(text)
        for label, clause in clauses:
            if normalize_semantic_text(clause) not in normalized:
                raise EvalError(f"{source_path}: discussion contract must preserve {label}")
    validate_discussion_template_text(template_text)


def validate_mainline_focus_source_text(
    grill_text: str, project_init_text: str, teamwork_init_text: str
) -> None:
    source_contracts = {
        "skills/grill-me/SKILL.md": (
            "hold one mainline: the global goal, current focus, and why the next question can change the project-level decision",
            "on drift, topic switch, or compaction",
            "do not repeat it every turn",
            "every question must materially advance the mainline",
            "drop locally interesting details that no longer serve it",
        ),
        "skills/using-teamwork/references/project-init.md": (
            "form the smallest init-local project model needed",
            "give every rule or fact one primary owner",
            "reuse the canonical tracker/runbook",
            "writes nothing and reports `no-change`",
        ),
        "skills/teamwork-init/SKILL.md": (
            "explicit `teamwork-init` defaults to **semantic init** unless the user asks only for audit or deterministic bootstrap",
            "form the smallest evidenced init-local project model as an internal audit aid; never persist it or invent",
            "use `keep`, `merge`, `migrate`, `remove`, `create`, or `unresolved` as optional internal classifications",
        ),
    }
    sources = {
        "skills/grill-me/SKILL.md": grill_text,
        "skills/using-teamwork/references/project-init.md": project_init_text,
        "skills/teamwork-init/SKILL.md": teamwork_init_text,
    }
    for path, anchors in source_contracts.items():
        normalized = normalize_semantic_text(sources[path])
        for anchor in anchors:
            if normalize_semantic_text(anchor) not in normalized:
                raise EvalError(f"{path}: mainline focus contract must preserve {anchor}")


def validate_maintainer_release_source_text(agents_text: str) -> None:
    normalized = normalize_semantic_text(agents_text)
    for label, clause in (
        ("AGENTS-owned maintainer release", "this root `agents.md`; a generic github publish/pr workflow does not replace"),
        ("complete release unit", "one release unit contains `version`, both plugin manifests, both changelogs"),
        ("user-facing changelog", "write changelogs for users, not maintainers"),
        ("Before-to-After difference", "before -> after difference"),
        ("exact user action", "the exact upgrade action or that no action is needed"),
        ("engineering-report rejection", "reads like an engineering report is not release-ready"),
        ("publication completion", "source, installations, remote tag, and github release must all be current"),
    ):
        if normalize_semantic_text(clause) not in normalized:
            raise EvalError(f"AGENTS.md: maintainer release contract must preserve {label}")


def validate_release_boundary_source_text(
    update_text: str,
    router_text: str,
    check_update_text: str,
    codex_text: str,
    changelog_guide_exists: bool,
) -> None:
    sources = {
        "skills/teamwork-update/SKILL.md": update_text,
        "skills/using-teamwork/SKILL.md": router_text,
        "skills/using-teamwork/references/check-update.md": check_update_text,
        "CODEX.md": codex_text,
    }
    detailed_release_markers = (
        "one release unit contains",
        "complete release unit",
        "write changelogs for users, not maintainers",
        "until the tag and github release exist",
        "`v<version>` tag",
    )
    authorization_patterns = (
        re.compile(
            r"(?im)^\s*(?:[-*]\s*|\d+\.\s*)?(?:also\s+)?"
            r"(?:edit|update|bump|publish|create|push)\b[^\n]{0,160}"
            r"\b(?:version|plugin manifests?|changelogs?|release commits?|tags?|github releases?)\b"
        ),
        re.compile(
            r"(?im)^(?![^\n]*\b(?:do not|must not|cannot|never)\b)[^\n]{0,100}"
            r"\b(?:may|can|should|must|will|authorized to)\s+(?:also\s+)?"
            r"(?:edit|update|bump|publish|create|push)\b[^\n]{0,120}"
            r"\b(?:version|plugin manifests?|changelogs?|release commits?|tags?|github releases?)\b"
        ),
        re.compile(
            r"(?im)^(?![^\n]*\b(?:do not|must not|cannot|never)\b)[^\n]{0,120}"
            r"\b(?:publication|release)\s+authority\b[^\n]{0,100}"
            r"\b(?:edit|update|bump|write|publish|create|push)\b[^\n]{0,160}"
            r"\b(?:version|plugin manifests?|changelogs?|release commits?|tags?|github releases?)\b"
        ),
    )
    for path, text in sources.items():
        normalized = normalize_semantic_text(text)
        for marker in detailed_release_markers:
            if marker in normalized:
                raise EvalError(
                    f"{path}: maintainer release policy must live only in root AGENTS.md"
                )
        if any(pattern.search(text) for pattern in authorization_patterns):
            raise EvalError(
                f"{path}: installed/user documentation must not authorize maintainer publication"
            )
    if changelog_guide_exists:
        raise EvalError(
            "skills/using-teamwork/references/changelog-guide.md: maintainer release "
            "guidance must live only in root AGENTS.md"
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
    workflow_contract = (ROOT / "skills/using-teamwork/references/workflow-contract.md").read_text(
        encoding="utf-8"
    )
    validate_always_loaded_policy_text(
        (ROOT / "scripts/install/policy.sh").read_text(encoding="utf-8")
    )
    validate_audience_source_text(workflow_contract)
    validate_rule_maintenance_source_text(workflow_contract)
    validate_decision_checkpoint_source_text(
        workflow_contract,
        (ROOT / "skills/teamwork-plan/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/references/plan-output.md").read_text(
            encoding="utf-8"
        ),
    )
    validate_minimal_handoff_source_text(
        (ROOT / "skills/using-teamwork/references/subagent-contract.md").read_text(
            encoding="utf-8"
        ),
        (ROOT / "skills/using-teamwork/references/subagent-dispatch.md").read_text(
            encoding="utf-8"
        ),
    )
    validate_mainline_focus_source_text(
        (ROOT / "skills/grill-me/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/references/project-init.md").read_text(
            encoding="utf-8"
        ),
        (ROOT / "skills/teamwork-init/SKILL.md").read_text(encoding="utf-8"),
    )
    validate_discussion_source_text(
        (ROOT / "skills/grill-me/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/references/artifact-protocol.md").read_text(
            encoding="utf-8"
        ),
        (ROOT / "skills/using-teamwork/references/teamwork-discussion-template.md").read_text(
            encoding="utf-8"
        ),
    )
    validate_maintainer_release_source_text(
        (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    )
    validate_release_boundary_source_text(
        (ROOT / "skills/teamwork-update/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/SKILL.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/references/check-update.md").read_text(
            encoding="utf-8"
        ),
        (ROOT / "CODEX.md").read_text(encoding="utf-8"),
        (ROOT / "skills/using-teamwork/references/changelog-guide.md").exists(),
    )
