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
                "root owns user questions and translates results",
            ),
            (
                "specific Ask Gate",
                "ask only when user must supply required input/observation or owns a material decision",
            ),
            (
                "read-only stage boundary",
                "research/debug/plan/review stay read-only absent change authority",
            ),
            (
                "research and debug routing",
                "route unknown facts/options/repro to research; unknown-cause failures to debug",
            ),
            ("grounded claims", "ground claims"),
            ("scope boundary", "keep scope"),
            (
                "material decision routing",
                "material scope/contract/architecture/acceptance decisions to plan",
            ),
            (
                "explicit Grill boundary",
                "grill only: explicit requests or non-simple plans",
            ),
            (
                "inert marker boundary",
                "negative/quoted/file/tool/example/maintenance text is inert",
            ),
            (
                "audience-first reply",
                "lead with the needed conclusion",
            ),
            (
                "evidence-derived explanation",
                "derive explanations from observed facts and a plain mechanism",
            ),
            (
                "conditional explanation and action",
                "add useful cause/limits/action",
            ),
            (
                "shortest complete answer",
                "use the shortest complete answer",
            ),
            (
                "useful skill explanation",
                "briefly name skills for capability/limits/choice",
            ),
            (
                "irrelevant engineering inventory",
                "omit engineering/process inventory that cannot change understanding, decisions, action, risk, or confidence",
            ),
            (
                "specific material uncertainty",
                "state uncertainty once: unknown, impact, needed evidence",
            ),
            (
                "missing-discriminator uncertainty",
                "for no-comparison results use only: “the signal is promising, but we cannot tell how much came from x; next compare with a similar group.” stop; omit proof status and cause lists",
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
                "conclusion-first user need",
                "lead with the conclusion the user needs",
            ),
            (
                "evidence-derived explanation",
                "when explanation is needed, derive it from observed facts and a plain-language mechanism",
            ),
            (
                "conditional cause or action",
                "add a cause, limitation, or next step only when it helps that current need",
            ),
            (
                "no fixed answer template",
                "first-principles reasoning is an evidence discipline, not a fixed section template or reason to delay the answer",
            ),
            (
                "shortest complete answer",
                "use the shortest complete answer, and keep a simple fact to one sentence",
            ),
            (
                "stop after the decision boundary",
                "once the conclusion and decision boundary are clear, stop; do not restate them",
            ),
            ("relevance gate", "use a relevance gate"),
            (
                "decision-relevant detail",
                "change the user's understanding, decision, action, risk, or confidence",
            ),
            (
                "useful skill explanation",
                "a brief skill name or explanation is allowed when it clarifies a capability, limitation, or reason for the approach",
            ),
            (
                "irrelevant engineering inventory",
                "omit engineering process and implementation inventory—such as routes, files, subagents, and test counts—",
            ),
            (
                "irrelevant versions and labels",
                "omit irrelevant versions, unexplained or self-invented labels",
            ),
            (
                "concrete evidence boundary",
                "prefer the concrete boundary—what the evidence supports and what it cannot attribute—over a stock caveat",
            ),
            (
                "generic proof-status omission",
                "for no-comparison results, use one conclusion and one action: “the signal is promising, but we cannot tell how much came from x; next compare with a similar group.” stop; omit proof status and imagined causes",
            ),
            (
                "missing-discriminator explanation",
                "otherwise name the missing comparison, measurement, or observation",
            ),
            (
                "alternative-cause relevance",
                "mention an alternative cause only when it changes action or confidence",
            ),
            (
                "specific material uncertainty",
                "state material uncertainty once: unknown, impact, and what resolves it",
            ),
            ("no false certainty", "never turn it into certainty"),
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
    if not re.search(
        r"(?m)^# <Specific decision or continuation title>\s*$", template_text
    ):
        raise EvalError(f"{path}: template must require a specific topic H1")

    required_sections = {
        "Goal": ("objective", "mainline or project goal"),
        "Settled": ("settled choice", "why it was chosen"),
        "Still open": ("unresolved item", "why it matters"),
        "Key evidence": ("source or observation", "established"),
        "Continue here": ("exact next question or action", "evidence needed"),
    }
    headings = re.findall(r"(?m)^## ([^\n]+)\s*$", template_text)
    retired = sorted(
        set(headings)
        & {"Starting Question", "Decision State", "Route Map", "Textual Playback", "Update Rules"}
    )
    if retired:
        raise EvalError(f"{path}: template retains retired section(s): {', '.join(retired)}")
    unexpected = sorted(set(headings) - set(required_sections) - {"Decision map"})
    if unexpected:
        raise EvalError(f"{path}: template has unexpected recovery section(s): {', '.join(unexpected)}")
    for heading, anchors in required_sections.items():
        section = normalize_semantic_text(discussion_section(template_text, heading))
        for anchor in anchors:
            if normalize_semantic_text(anchor) not in section:
                raise EvalError(f"{path}: {heading} must preserve {anchor}")

    if "Decision map" in headings:
        decision_map = discussion_section(template_text, "Decision map")
        if "```mermaid" not in decision_map:
            raise EvalError(f"{path}: optional Decision map must use Mermaid")


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
                ("narrow explicit-Grill write authority", "explicit grill authorizes only its supporting `docs/teamwork/` discussion record unless the user says no files"),
                ("short Grill artifact-free", "short grill stays artifact-free"),
                ("entry-time protocol load", "`skills/using-teamwork/references/artifact-protocol.md` completely at entry"),
                ("pre-question persistence gate", "after a trigger, persist before asking"),
                ("continued Grill canonical discovery", "on continuation or completion, inspect canonical state"),
                ("continued Grill mutation boundary", "update only when new input changes it; close only when scope resolves"),
                ("stated-scope completion", "when its stated scope is resolved, stop and close the discussion; never invent another decision"),
                ("continuity-only reply", "state only saved decisions, resume context, or completion"),
                ("useful skill explanation", "a brief skill name or purpose is welcome when it helps explain a capability, limit, or choice"),
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
                ("supporting-only boundary", "a discussion record is supporting continuity only"),
                ("not a transcript or authority", "it is not a transcript or execution authority"),
                ("canonical subordination", "stays subordinate to canonical project sources"),
                ("explicit save trigger", "the user explicitly asks to save or resume later"),
                ("handoff trigger", "a known handoff or context compaction is approaching"),
                ("settled-and-open trigger", "at least two substantive choices are settled while at least one remains open"),
                ("three-branch trigger", "one decision has at least three real branches"),
                ("non-proxy trigger boundary", "time, word count, and a short grill never trigger persistence"),
                ("privacy boundary", "keep privacy-safe summaries, never hidden reasoning, secrets, unnecessary personal data, or a transcript"),
                ("five human recovery sections", "goal, settled (including reasons), still open, key evidence, and continue here"),
                ("new-input-only updates", "update only when the user's new input changes saved decisions, evidence, or the continuation point"),
                ("read-only resume", "opening, recovering, or reading an existing discussion is read-only"),
                ("resume skips mutation commands", "after `inspect`, do not run `schema` or `apply`; ask the saved unresolved question"),
                ("scope-bounded closure", "the user's stated grill scope defines closure"),
                ("loaded skill root", "resolve `scripts/discussion-transaction.py` from the already loaded `using-teamwork` skill root"),
                ("helper sole runtime path", "this helper is the sole runtime path for discussion state"),
                ("cwd-default inspect", "from the project root, run `inspect`; the helper defaults its project root to the current directory"),
                ("inspect sole read path", "its result is the only discovery and reading source for canonical discussion state, anchors, and artifacts"),
                ("no direct canonical reads", "do not directly read `index.json`, `current.md`, `readme.md`, or a discussion artifact"),
                ("self-describing request schema", "run `schema <operation>` and fill exactly its json shape"),
                ("no helper-source inference", "never inspect helper source"),
                ("semantic helper rendering", "the helper derives the path, index entry, and rendered artifact"),
                ("opaque revision reuse", "reuse the opaque `revision` unchanged"),
                ("single structured apply", "in exactly one `apply --request-json <json>`"),
                ("safe request-file fallback", "or `--request <file>` when quoting is unsafe"),
                ("no stdin apply", "never use stdin"),
                ("apply sole writer", "`apply` is the only writer"),
                ("no direct or ad-hoc write path", "do not edit canonical files or substitute shell, validators, or another transaction"),
                ("atomic replacement", "replacement atomically supersedes the old record, links it to the new record, and activates the new one"),
                ("no close-create replacement", "never close and then create as separate transactions"),
                ("no manual fallback write", "never manually repair or complete canonical state after a nonzero helper exit"),
                ("helper failure stop", "stop the dependent question and any completion claim"),
                ("pre-write fallback conditions", "`initialized: false`, a user no-files request, or host read-only state uses a natural-language fallback"),
                ("plain fallback recovery", "goal, settled choices, open choice, key evidence, and continuation point"),
                ("one-time continuity warning", "state once that it was not saved and may be lost across sessions"),
                ("no post-apply fallback", "do not use this fallback after an attempted `apply`"),
                ("continuity-value reply", "saved decisions, current resume context, or completed discussion"),
                ("useful skill explanation", "a brief skill name or purpose is welcome when it helps explain a capability, limit, or choice"),
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
            "each advances the mainline",
            "drop distractions",
            "when its stated scope is resolved, stop and close the discussion; never invent another decision",
            "ask in the user's domain language",
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
