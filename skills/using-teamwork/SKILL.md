---
name: using-teamwork
description: Use when starting coding, debugging, research, planning, implementation, or review work where the task may be non-trivial, evidence-sensitive, cross-turn, cross-agent, high-risk, or goal-directed.
---

# Using Teamwork

Use this lightweight entrypoint to decide whether Teamwork adds value. Keep
simple work native; route only when evidence, planning, review, delegation, or
autonomous convergence materially improves correctness.

## Route Check

Use the narrowest matching stage:

| Signal | Route |
|---|---|
| Needs file, diff, log, artifact, or external evidence before choosing | `teamwork-research` |
| User asks for a plan, or first move affects scope/contract/verification | `teamwork-plan` |
| Accepted plan exists and needs implementation | `teamwork-execute` |
| Plan or completed work needs independent scrutiny | `teamwork-review` |
| User wants iteration until verified success, budget exhaustion, or blocker | `teamwork-goal` |

If none applies, continue normally without a route banner.

For goal-directed requests, route to `teamwork-goal` for a chat-only `Goal
Proposal` first when the objective, done evidence, scope, or stop rules are not
already explicit. Create or continue native Codex goal state only after the
user accepts that proposal, unless an active goal already exists.

## Native Default

Native flow is correct for single-step lookups, quick factual answers, trivial
one-liners, and small isolated edits with obvious verification. Do not create
artifacts, subagents, durable plans, or review passes for ceremony.

Before staying native for non-trivial work, answer:

1. What assumption could change behavior, scope, contract, or verification?
2. What is the smallest sufficient path?
3. What is in scope and out of scope?
4. What concrete check proves success?

If those answers are unclear, route to `teamwork-research` or `teamwork-plan`.

## Codex Fit

- Codex native capabilities are the substrate; Teamwork strengthens their use
  with evidence, artifacts, routing, review, and failure-iteration policy.
- `update_plan` is visible progress only, not a durable plan.
- Use native Codex goals only for explicit autonomous convergence or an active
  goal.
- Use Codex subagents for independent evidence, scoped Worker execution, or
  fresh-context review when an accepted Goal Proposal or durable plan includes
  Subagent Routing, or when the user explicitly asks.
- Do not bypass sandbox or approval policy.
