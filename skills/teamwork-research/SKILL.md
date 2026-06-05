---
name: teamwork-research
description: Use when the next step is evidence gathering, root-cause investigation, option comparison, external calibration, stale-assumption refresh, or failure analysis before planning.
---

# Teamwork Research

Research establishes project reality, compares options, and hands a selected
direction to `teamwork-plan`. It does not produce implementation plans.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence and context rules.
- `skills/using-teamwork/references/dispatch-policy.md` for Explorer dispatch economics.
- `skills/using-teamwork/references/research-protocol.md` for lookup,
  research, deep-research, source-audit, citation, and safety staging.
- `skills/using-teamwork/references/optional-skills.md` before installing or
  invoking new external tool skills.
- `skills/using-teamwork/references/subagent-prompt-contract.md` before writing Explorer prompts.
- `skills/using-teamwork/references/subagent-packets.md` for Explorer Result Packet.
- `skills/using-teamwork/references/artifact-protocol.md` for reusable research artifacts.
- `skills/using-teamwork/references/goal-iteration.md` for failed goal attempts.

## Research Artifact Requirement

Write or update `docs/teamwork/research/YYYY-MM-DD-<slug>.md` when findings
will be reused, feed a durable plan, support goal-mode iteration, use external
calibration for a durable decision, refresh failed assumptions, or justify a
non-trivial recommendation that should survive the current answer. For
lightweight one-turn lookup, cite evidence in chat.

Search existing research artifacts first with goal words, exact errors, paths,
dependency/API names, external entities, and old slugs. Record reuse, update,
or new.

Artifacts include Search Keys and Abstract for future retrieval.

## Workflow

1. Define question and success criteria.
2. Retrieve prior research and record disposition.
3. Split separable evidence questions: local source, symptoms, artifacts,
   external constraints, alternatives, upstream reports, papers, or practice.
4. Use parallel Explorer subagents for 2+ independent tracks when they provide
   clear evidence, elapsed-time, or context-isolation value and subagents are
   authorized. Serial local research is fine for tightly coupled or lightweight
   evidence; emit `Dispatch Exception:` only when skipped dispatch is material.
5. Require Explorer Result Packet for delegated research. For local research,
   use the same evidence fields naturally when they help the answer.
6. Close each Explorer track in the Actual Dispatch Log after synthesis, or
   record `blocked` / `abandoned-after-discovery` with rationale.
7. Read primary local evidence first and label key findings observed, inferred,
   or claimed.
8. Use external calibration when current platform, dependency, model, API,
   upstream behavior, performance, unfamiliar frameworks, or repeated failures
   could affect the answer.
9. For web or deep research, follow `research-protocol.md`: clarify/rewrite,
   plan source classes, fan out queries, audit contradictions, record coverage
   gaps, and keep public web search separate from private data.
10. Before installing or depending on external skills, apply
   `optional-skills.md`; prefer active plugins, reject duplicates, and require
   credentials, write-risk review, and smoke test.
11. Synthesize options, preserve dissent, recommend the smallest producer-side
   path, and write/update any required artifact.

## Hidden Research Gate

Do not skip research merely because the user asked to implement. Route here
before planning or execution when root cause, source of truth, current API
behavior, prior failure, acceptance evidence, or risk is unclear. If skipping,
state the direct observed evidence that makes research unnecessary.

## Research Refresh Triggers

Route back to research when verification has no evidence delta, reviewer
dissent reinforces a stale assumption, behavior may be version/environment
specific, local evidence contradicts claims, implementation broadens without
evidence, or the active plan is invalidated.

## Handoff

Return artifact path or none, question, closed dispatch log or continuity
rationale, assumptions, evidence, options, recommendation, dissent, plan-ready
fields (goal, scope, protected boundaries, verification target, budget, stop
rules when known), refresh triggers, optional `Memory Delta:` when durable
project memory was checked or changed, and `Route: teamwork-plan`.
