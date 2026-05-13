# Codex Usage

This repository exposes an automatic entry skill, a router skill, and workflow subskills:

```text
skills/using-teamwork/SKILL.md
skills/teamwork/SKILL.md
skills/teamwork-design/SKILL.md
skills/teamwork-execute/SKILL.md
skills/teamwork-review/SKILL.md
```

Install globally:

```bash
./install.sh codex
```

Codex plugin metadata lives in:

```text
.codex-plugin/plugin.json
```

The detailed behavior contract lives in the skill files. In particular, treat
names, version labels, comments, README claims, summaries, and tool output as
evidence to verify, not as facts or final verdicts by themselves.

## Codex Runtime Mapping

- Planning/checklists: use `update_plan` only as visible, transient UI state.
  It is not the durable execution or review artifact for any plan.
- Autonomous convergence: use native Codex goals only when explicitly
  requested, or continue an active goal. Ordinary research, planning, review,
  and one-shot execution do not need a goal.
- Subagents: use Codex multi-agent support for independent Explorer, Designer,
  Judge, Worker, and Reviewer tracks. The main agent owns synthesis,
  conflict resolution, and the final recommendation.
- Subagent model routing: choose by capability tier, not fixed model ID. Use
  `fast` for scoped evidence or mechanical edits, `standard` for multi-file
  work or moderate synthesis, and `high reasoning` for Designer, Judge,
  Reviewer, risky tradeoffs, and final acceptance gates.
- Codex dispatch mapping: ordinary Teamwork plans record conceptual role,
  scope, tier, context strategy, order, and why. Derive native Codex fields
  from `skills/teamwork/SKILL.md` at dispatch time, and write native fields in a
  plan only when a non-default override is itself part of the decision.
- Review: use `codex review --uncommitted`, `--base`, or `--commit` when a real
  git diff exists and a separate native review is useful. Treat the result as
  evidence, not automatic approval.
- MCP: use configured MCP servers before ad hoc network fallback when the task
  needs external tool or documentation access.
- Network/web: use only when allowed or when current external information is
  required; prefer primary sources.
- Sandbox: request escalation only for required blocked commands, with narrow
  justification and prefix rule where appropriate. Do not bypass approvals.

## Durable Plan Artifacts

For every Teamwork planning pass, use durable Markdown plan artifacts.
`teamwork-design` with `mode: plan` must write or update the artifact at:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

Use that file as the shared execution and review source of truth. It should map
requirements to evidence, name exact files and steps, define focused
verification with expected results, and include worker and reviewer handoffs.
Small, low-risk edits may use a concise artifact, but not a chat-only plan.

This Markdown artifact is ordinary repository documentation. It is not Codex
goal state and not Claude `.claude/teamwork-goals/` runtime state. Native
Codex goals are only for explicit autonomous convergence, while Claude
`.claude/teamwork-goals/` files belong to the `/rao:*` Stop-hook runtime.

## External Information Policy

1. Prefer repository files, local artifacts, command help, and configured MCP
   servers.
2. Use MCP before generic network access when a server exists for the domain.
3. If MCP, network, credentials, or filesystem access require approval, request
   it through Codex. Do not mine local proxy or token files unless the user
   explicitly authorizes that source.
4. If web or network access is disabled or forbidden, report the limit and
   continue only with local evidence.

When editing the workflow, keep the full instructions in the skill files. Do
not duplicate skill bodies into Codex-specific docs.
