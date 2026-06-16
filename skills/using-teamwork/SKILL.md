---
name: using-teamwork
description: Use when starting any coding-agent task: route to native/research/plan/execute/review/goal/init/update.
---

# Using Teamwork

Teamwork sits on native tools: native capabilities execute; Teamwork adds
evidence, dispatch, memory, and acceptance. Default to acting directly on clear
work; escalate only when it improves correctness, continuity, or cost.

Read `references/workflow-contract.md` for the shared principles, judgment, and
platform map. Load other references only when their stage needs them.

## First: can you proceed?

Default to proceeding. Ask one short question first only when you hit a real
obstacle, lack information you cannot obtain yourself, or face a core decision
you cannot resolve — scope, acceptance, a required value, an irreversible
action, or public behavior. Decide routine matters (tool/MCP choice, naming,
approach) yourself. Do not narrate this as a gate.

## Route

Pick the stage that matches the work. Most small, clear tasks need none of
them — just do the work natively.

- **Stay native** — quick facts, read-only answers, tiny edits, low-risk bug
  fixes, low-risk mechanical multi-file edits, one CodeGraph question, or a
  tightly coupled critical path. Write naturally; no artifacts or ceremony.
- **Research** (`skills/teamwork-research/SKILL.md`) — root cause, source/API
  behavior, failure evidence, stale assumptions, or option comparison is
  unclear.
- **Plan** (`skills/teamwork-plan/SKILL.md`) — explicit plan/design request, or
  non-trivial implementation that needs scope, verification, or dispatch.
- **Execute** (`skills/teamwork-execute/SKILL.md`) — "go ahead", "do it",
  "continue", "resume" on an accepted plan.
- **Review** (`skills/teamwork-review/SKILL.md`) — "review", "diff", or check
  completed non-lightweight work. Simple checks stay native.
- **Goal** (`skills/teamwork-goal/SKILL.md`) — "keep going", "until it passes",
  or budgeted iteration to a verified target.
- **Init** (`skills/teamwork-init/SKILL.md`) — "init", "AGENTS/CODEX/CURSOR/
  CLAUDE", or slim project instructions.
- **Update** (`skills/teamwork-update/SKILL.md`) — "version", "release",
  "bump", or refresh the installed package.

Routing is automatic from intent; you do not wait for the user to name a stage.

## Orchestrate

When the work is non-lightweight and an independent track can run in parallel
with clear ownership, fan out subagents to go faster — proactively, without
waiting for the user to ask. The main agent stays the orchestrator: it owns
scope, integration, final verification, and acceptance. See
`references/subagent-dispatch.md`.

For required acceptance of non-lightweight work, prefer a fresh-context
Reviewer; if subagents are unavailable, say so and name the residual risk.

## Output

For lightweight native work, just answer. Reserve a short `Route: ...` line for
non-lightweight handoffs, redirects, blockers, or goal/update work. Include
`Memory Delta:` only when durable project memory was checked or changed.
