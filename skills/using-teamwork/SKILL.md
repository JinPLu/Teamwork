---
name: using-teamwork
description: Use when starting any coding-agent task including coding, debugging, implementation, planning, review, evidence gathering, accepted-plan execution, package updates, or goal-directed work.
---

# Using Teamwork

Teamwork is a Codex-first platform-native layer. Codex, Cursor, or Claude Code
does the work; Teamwork adds evidence, dispatch, review, memory, and goals.
Labels: observed, inferred, claimed.

## References

Load references only when needed.
`references/workflow-contract.md` owns judgment and Platform Native Policy Map;
`dispatch-policy.md` dispatch; `platform-dispatch-mapping.md` native fields;
`workflow-orchestration.md` swarms; `artifact-protocol.md` memory.

## Route Check

Evidence -> `skills/teamwork-research/SKILL.md`; init/slim -> `skills/teamwork-init/SKILL.md`; plan -> `skills/teamwork-plan/SKILL.md`; execute accepted plan -> `skills/teamwork-execute/SKILL.md`; review -> `skills/teamwork-review/SKILL.md`; update -> `skills/teamwork-update/SKILL.md`; goal loop -> `skills/teamwork-goal/SKILL.md`.

## Automatic Stage Selection

Do not wait for named skills when intent is clear; discovery reads frontmatter
before routing.

- Planning: "plan", "design", "figure out", non-trivial "implement/fix/add/change";
  unclear human goal/scope/acceptance asks first; unclear root/source/API/failure/evidence/risk routes research first.
- Init: "init", "initialize", "AGENTS", "CODEX", "CURSOR", "CLAUDE", "slim instructions".
- Execution: "go ahead", "execute", "continue", "resume", "do it".
- Review: "review", "diff", or "check/validate completed work";
  simple checks stay native.
- Update: "version", "release", "changelog", "bump".
- Goal: "keep going", "until it passes", "iterate until done", or explicit
  budgeted convergence.

For convergence, route to `teamwork-goal` for chat-only `Goal Proposal`
before platform goal handoff unless active goal state exists.

## Orchestration Default

Native fast path: stay in platform flow for quick facts, tiny edits, low-risk
bug fixes, low-risk mechanical multi-file edits, credential work, tight
critical path, one CodeGraph-answerable structural question, or higher subagent
context cost. Do not create artifacts, subagents, durable plans, packets, or
review ceremony for lightweight work.

For durable memory, check `docs/teamwork/index.json`, then `active.current` or
`docs/teamwork/current.md` before deeper artifact reads.

Before staying native for non-trivial work, state scope, path, protected
boundary, and success check. Route unclear root cause, public behavior,
protected contracts, stale assumptions, or acceptance evidence to research or
planning.

When Teamwork is active, the main agent orchestrates. If subagents are
authorized, dispatch proactively when an independent track has clear evidence,
elapsed-time, context-isolation, ownership, or fresh-review value: Explorer,
Designer, Judge, Worker, or Reviewer. Use fresh review when available for
required acceptance; otherwise report unreviewed risk.

Plans may suggest routing; stage dispatch need not wait for named tracks. On
Codex, standing instructions can satisfy explicit subagent request; without
authorization, keep local and record the exception.

Before treating subagents as unavailable for work that needs them, use the
Subagent Tool Discovery Gate. Skipped material dispatch needs
`Dispatch Exception:`; if required fresh review is unavailable, missing
authorization, or user-disabled, label the acceptance `unreviewed`.

## Route Output

Use route banners only for non-lightweight handoffs, redirects, blockers,
goal/update work, or material dispatch/artifact state: `Route: ...`.

For lightweight native flow, write naturally. Include `Memory Delta:` only for
checked/changed durable memory.
