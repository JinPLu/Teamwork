---
name: using-teamwork
description: Use when starting any coding-agent task: route to native/research/plan/execute/review/goal/init/update.
---

# Using Teamwork

Teamwork is a platform-native layer: native tools execute; Teamwork adds evidence, dispatch, and memory.
Labels: observed, inferred, claimed.

## Progressive Reference Loading

| Condition | Load |
|---|---|
| judgment, boundaries, Platform Native Policy Map | `references/workflow-contract.md` |
| dispatch economics | `dispatch-policy.md` |
| native dispatch fields | `platform-dispatch-mapping.md` |
| swarm workflow | `workflow-orchestration.md` |
| durable memory | `artifact-protocol.md` |

## Route Check

Evidence -> `skills/teamwork-research/SKILL.md`; init/slim -> `skills/teamwork-init/SKILL.md`; plan -> `skills/teamwork-plan/SKILL.md`; accepted continuation -> `skills/teamwork-execute/SKILL.md`; review -> `skills/teamwork-review/SKILL.md`; update -> `skills/teamwork-update/SKILL.md`; convergence -> `skills/teamwork-goal/SKILL.md`.

## Automatic Stage Selection

Do not wait for named skills when intent is clear; discovery reads frontmatter before route filtering. Clarification-first routing comes before any Native fast path. Router Gate: Fast = clarified lightweight Native; Ask = missing human needs; Research = unclear evidence/root/stale/options; Design = non-trivial scope/verification/dispatch/acceptance; Review = completed work or non-lightweight acceptance.

- Native: quick facts, tiny edits, low-risk bugs, low-risk mechanical multi-file edits, credentials, tight path, one CodeGraph question.
- Research: unclear root, source/API behavior, failure evidence, stale assumptions, or options.
- Plan: explicit plan/design or non-trivial implementation needing scope/verification/dispatch/memory; unclear human goal/scope/acceptance asks first, not guessed.
- Execute: "go ahead", "execute", "continue", "resume", "do it".
- Review: "review", "diff", or "check/validate completed work"; simple checks stay native.
- Init: "init", "initialize", "AGENTS", "CODEX", "CURSOR", "CLAUDE", "slim instructions".
- Update: "version", "release", "changelog", "bump".
- Goal: "keep going", "until it passes", "iterate until done", or budgeted convergence.

For convergence, route to `teamwork-goal` for chat-only `Goal Proposal` before platform goal handoff unless active goal state exists.

## Orchestration Default

For lightweight work after clarification, write naturally. Do not create artifacts, subagents, durable plans, packets, route banners, or ceremony.

Before staying native for non-trivial work, state scope, path, boundary, and success check.

For non-lightweight tasks, keep a short Confidence Ledger: evidence known, assumptions/questions, verification target, and residual risk.

When Teamwork is active, the main agent orchestrates. If subagents are authorized, dispatch proactively when an independent track has clear evidence, elapsed-time, isolation, ownership, or review value; prefer fanout for non-lightweight research, design/plan review, and fresh execution review. Use fresh review for required acceptance; otherwise report unreviewed risk.

Plans may suggest routing; they are not the only dispatch authorization. Use the Subagent Tool Discovery Gate before unavailable claims. Skipped material dispatch needs `Dispatch Exception:`.

## Route Output

Use route banners only for non-lightweight handoffs, redirects, blockers, goal/update work, or material dispatch/artifact state: `Route: ...`.

For lightweight native flow, write naturally. Include `Memory Delta:` only for checked/changed durable memory.
