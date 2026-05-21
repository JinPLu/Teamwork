---
name: using-teamwork
description: Use when starting any coding, debugging, research, planning, implementation, or review conversation — invoke before multi-step or non-trivial work to decide whether a Teamwork stage would improve the outcome. When in doubt, invoke this skill first.
---

# Using Teamwork

Use this lightweight preference router at the start of normal coding-agent work.
Its purpose is to decide whether Teamwork adds value without blocking the host
agent from using native strengths. In Codex, that means using native planning
UI, subagents, goals, sandbox approvals, and reviews instead of emulating
Claude hook behavior. Keep progress anchored to the active objective, plan or
execution memo, verification target, and review result instead of maintaining
long process state in the main thread.

## Rule

Before answering or acting on any multi-step or non-trivial request, ask: does a
Teamwork stage apply here? A stage applies when **any** of these are true:

- Answering correctly requires reading files, diffs, logs, or external sources
  before choosing an approach → `teamwork-research`
- The task has multiple steps where a wrong first move wastes significant effort,
  or the user asks for a plan → `teamwork-plan`
- An accepted plan exists and needs to be implemented → `teamwork-execute`
- A plan or completed implementation needs a reviewer check → `teamwork-review`
- The user asks to run until it passes, iterate until done, or converge on a
  verifiable target → `teamwork-goal`

If any applies, invoke the narrowest matching skill before continuing. Do not
substitute native tools for the skill just because the task seems manageable.

## Codex Runtime Fit

When running in Codex:

- Keep simple tasks native.
- Use `update_plan` only for visible progress; it is not the durable plan.
- Use Codex subagents for independent evidence, scoped Worker execution, or
  fresh-context review. For non-lightweight work, split independent tracks
  first and dispatch useful subagents early while the main thread continues
  non-overlapping work.
- When Teamwork is active, treat the user as granting standing authorization
  for automatic subagent delegation on independent non-lightweight tracks. Do
  not ask for extra "fan out" confirmation unless the dispatch would need new
  credentials, destructive actions, unclear write ownership, or another
  approval-gated capability.
- Use native Codex goals only for explicit autonomous convergence requests or
  an already active goal.
- Use sandbox escalation only when a required command is blocked; do not bypass
  approvals.

## Default: Native Flow First

Simple, single-step, directly answerable tasks stay in native flow. Do not
create durable plans, invoke subagents, or add review passes when they would
only add ceremony.

**Simple**: single-file lookup, quick factual answer, trivial one-liner, or a
small isolated change with an obvious correct action.

**Not simple**: multiple files or steps, uncertain scope, downstream
dependencies, high-risk changes, or results the user will build on later.

## Behavior Check

Before routing or staying native for non-trivial work, answer four questions:

1. What assumption could change the behavior, scope, contract, or verification?
2. What is the smallest sufficient path that solves the user's actual goal?
3. What exact files, claims, or decisions are in scope, and what is out of
   scope?
4. What progress anchor, concrete check, artifact, or observation will prove
   the work succeeded?

If these answers are unclear, route to `teamwork-research` or `teamwork-plan`.
If they are obvious and the work is simple, continue in native flow without
adding Teamwork ceremony.

## Routing Quick Reference

| User signal | Invoke |
|---|---|
| "research X", "why is X failing", "what options do we have", "investigate" | `teamwork-research` |
| "make a plan", "plan before we code", complex multi-step change | `teamwork-plan` |
| "implement the plan", "execute", accepted plan in context | `teamwork-execute` |
| "review this plan", "review the diff", "is this correct" | `teamwork-review` |
| "run until it passes", "keep going", "iterate until done", verifiable target + budget | `teamwork-goal` |

## Don't Rationalize

These thoughts mean a stage skill likely applies:

| Thought | What it usually means |
|---|---|
| "I already know the answer" | Verify first when correctness depends on files, logs, external behavior, or current state. |
| "This is just a small change" | Check whether it is truly simple; if scope or verification is unclear, plan first. |
| "I'll figure out the plan as I go" | That's when scope creep happens. |
| "Review feels redundant here" | High-risk work needs it most. |
| "native flow is fine for this" | Check the criteria above first. |

## Discipline

Start from local repository evidence, then use external calibration for
non-trivial research where current platform, dependency, model, prompt, or
upstream behavior could affect the answer. Keep assumptions explicit, choose
simple and surgical changes, verify against the user's goal, and keep the main
agent responsible for synthesis, verification, and final acceptance.

If no stage applies after checking the criteria above, continue normally.
