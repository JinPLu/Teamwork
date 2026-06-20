---
name: teamwork-research
description: Use when the next step is evidence gathering, source-of-truth lookup, repro-surface framing, option comparison, external calibration, or stale-assumption refresh before planning/debugging.
---

# Teamwork Research

Research establishes project reality, compares options, and hands a direction to
`teamwork-plan` or `teamwork-debug`. It does not produce implementation plans.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence rules; `skills/using-teamwork/references/research-protocol.md` for
lookup/research/deep modes and source-census; `skills/using-teamwork/references/subagent-dispatch.md`
and `skills/using-teamwork/references/subagent-contract.md` for Explorer fan-out;
`skills/using-teamwork/references/artifact-protocol.md` for reusable findings;
`skills/using-teamwork/references/debug-mode.md` for the runtime-diagnosis
boundary;
`skills/using-teamwork/references/optional-skills.md` before external tools.

## When To Use

Route here before planning or execution when source of truth, current API
behavior, repro surface, prior evidence, acceptance evidence, or risk is
unclear. Route to `teamwork-debug` instead when the bug is reproducible or
likely reproducible and runtime evidence can decide the cause.
If you skip it, state the direct observed evidence that makes research
unnecessary.

## Workflow

1. Define the question and what a good answer looks like.
2. Search prior artifacts; record reuse, update, or new.
3. Split separable evidence questions: local source, symptoms, external
   constraints, alternatives, upstream reports, papers, or practice.
4. Fan out parallel Explorers for 2+ independent tracks when they add evidence,
   time, or context-isolation value and subagents are authorized. Keep tightly
   coupled or one-track evidence local.
5. Read primary local evidence first; label findings `observed`, `inferred`, or
   `claimed`.
6. Use external calibration when platform, dependency, model, API, or upstream
   behavior could change the answer; follow `research-protocol.md` for web/deep
   work and keep public web search separate from private data.
7. Synthesize options, preserve dissent, recommend the smallest producer-side
   path, and write any reusable artifact.

## Artifacts

Write `docs/teamwork/research/YYYY-MM-DD-<slug>.md` when findings will be reused,
feed a durable plan, support goal-mode iteration, or justify a non-trivial
recommendation. For one-turn lookup, cite evidence in chat. Artifacts include
Search Keys and an Abstract for retrieval. For broad research, keep recall broad
but transport narrow: condensed Explorer packets plus artifact pointers, not raw
dumps in the main thread.

## Handoff

Return artifact path or none, the question, a closed dispatch log or continuity
rationale, assumptions, evidence, options, recommendation, dissent, and
plan-ready fields (goal, scope, protected boundaries, verification target,
budget, stop rules when known). Include `Memory Delta:` only when durable
project memory was checked or changed. End with `Route: teamwork-debug` when
runtime diagnosis is next, or `Route: teamwork-plan` when a plan is next.
