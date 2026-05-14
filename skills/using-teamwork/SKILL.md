---
name: using-teamwork
description: Use when starting any coding, debugging, research, planning, implementation, or review conversation - establishes automatic Teamwork routing before normal work begins.
---

# Using Teamwork

Use this lightweight router at the start of normal Codex work. Its purpose is
to make Teamwork automatic without loading the larger stage skills until the
request shape is known.

## Rule

Before answering or acting on coding, debugging, repository research,
experimental analysis, implementation planning, code modification,
verification, or review requests, decide whether a Teamwork stage applies.
If a stage applies, invoke the narrowest Teamwork skill before continuing.

Do not use Teamwork for purely casual chat, simple factual answers with no
workflow value, or requests where the user explicitly says not to use it.

## Route

- Use `teamwork-design` with `mode: research` when the next step is evidence
  gathering, option comparison, root-cause investigation, or tradeoff analysis.
- Use `teamwork-design` with `mode: plan` when the user asks for a plan or a
  non-lightweight change needs an executable plan before editing.
- Use `teamwork-review` with `mode: plan` when reviewing a proposed plan before
  implementation.
- Use `teamwork-execute` when an accepted Teamwork plan should be implemented.
- Use `teamwork-review` with `mode: execution` before claiming a non-trivial
  implementation is complete.
- Use `teamwork-goal` with `mode: goal` only when the user asks for autonomous
  convergence, such as running until a verifiable target passes or a budget is
  exhausted.

## Discipline

Teamwork is evidence-first and scoped. Prefer local repository evidence before
external sources. Use subagents only when independent tracks make the result
faster or more reliable, and keep the main agent responsible for synthesis,
verification, conflict resolution, and final acceptance.

If no Teamwork stage applies, continue normally and keep the response concise.
