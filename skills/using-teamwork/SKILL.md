---
name: using-teamwork
description: Use when starting any coding-agent task: route to fast path, research, plan, execute, review, goal, init, or update; escalate only when evidence, scope, delegation, or acceptance needs it.
---

# Using Teamwork

Teamwork is a platform-native layer. Native tools work; Teamwork adds evidence,
dispatch, memory, and goals.
Labels: observed, inferred, claimed.

## Progressive Reference Loading

Load the needed reference:

| Condition | Load |
|---|---|
| judgment, boundaries, Platform Native Policy Map | `references/workflow-contract.md` |
| dispatch economics | `dispatch-policy.md` |
| native dispatch fields | `platform-dispatch-mapping.md` |
| swarm workflow | `workflow-orchestration.md` |
| durable memory | `artifact-protocol.md` |

## Route Check

Evidence -> `skills/teamwork-research/SKILL.md`; init/slim ->
`skills/teamwork-init/SKILL.md`; plan -> `skills/teamwork-plan/SKILL.md`;
accepted continuation -> `skills/teamwork-execute/SKILL.md`; review ->
`skills/teamwork-review/SKILL.md`; update -> `skills/teamwork-update/SKILL.md`;
convergence -> `skills/teamwork-goal/SKILL.md`.

## Automatic Stage Selection

Do not wait for named skills when intent is clear; discovery reads frontmatter
before route filtering. Native fast path; Fast path first:

- Native: quick facts, tiny edits, low-risk bug fixes, low-risk mechanical multi-file edits,
  credentials, tight critical path, one CodeGraph question.
- Research: unclear root, source/API behavior, failure evidence, stale
  assumptions, or options.
- Plan: explicit plan/design, fuzzy feature shaping, or non-trivial
  implementation needing scope, verification, dispatch, or memory; unclear human goal/scope/acceptance asks first.
- Execute: "go ahead", "execute", "continue", "resume", "do it".
- Review: "review", "diff", or "check/validate completed work"; simple checks stay native.
- Init: "init", "initialize", "AGENTS", "CODEX", "CURSOR", "CLAUDE", "slim instructions".
- Update: "version", "release", "changelog", "bump".
- Goal: "keep going", "until it passes", "iterate until done", or budgeted convergence.

For convergence, route to `teamwork-goal` for chat-only `Goal Proposal` before
platform goal handoff unless active goal state exists.

## Orchestration Default

For lightweight work, write naturally. Do not create artifacts, subagents,
durable plans, packets, route banners, or review ceremony.

Before staying native for non-trivial work, state scope, path, boundary, and
success check. Use plan-as-you-go when clear; durable planning only when the
boundary must survive the turn.

When Teamwork is active, the main agent orchestrates. If subagents are
authorized, dispatch proactively when an independent track has clear evidence,
elapsed-time, context-isolation, ownership, or fresh-review value: Explorer,
Designer, Judge, Worker, or Reviewer. Use fresh review when available for
required acceptance; otherwise report unreviewed risk.

Plans may suggest routing; they are not the only dispatch authorization. Before
treating subagents as unavailable for work that needs them, use the
Subagent Tool Discovery Gate. Skipped material dispatch needs
`Dispatch Exception:`; if required fresh review is unavailable, missing
authorization, or user-disabled, label the acceptance `unreviewed`.

## Route Output

Use route banners only for non-lightweight handoffs, redirects, blockers,
goal/update work, or material dispatch/artifact state: `Route: ...`.

For lightweight native flow, write naturally. Include `Memory Delta:` only for
checked/changed durable memory.
