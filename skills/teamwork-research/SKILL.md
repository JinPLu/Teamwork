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
- `skills/using-teamwork/references/subagent-prompt-contract.md` before writing Explorer prompts.
- `skills/using-teamwork/references/subagent-packets.md` for Explorer Result Packet.
- `skills/using-teamwork/references/artifact-protocol.md` for reusable research artifacts.
- `skills/using-teamwork/references/goal-iteration.md` for failed goal attempts.

## Research Artifact Requirement

Write or update `docs/teamwork/research/YYYY-MM-DD-<slug>.md` when findings
will be reused, feed a durable plan, support goal-mode iteration, use external
calibration, refresh failed assumptions, or justify a non-trivial
recommendation. For lightweight one-turn lookup, cite evidence in chat.

Search existing research artifacts first with goal words, exact errors, paths,
dependency/API names, external entities, and old slugs. Record reuse, update,
or new.

Artifacts include Search Keys and Abstract for future retrieval.

## Workflow

1. Define question and success criteria.
2. Retrieve prior research and record disposition.
3. Split separable evidence questions: local source, symptoms, artifacts,
   external constraints, alternatives, upstream reports, papers, or practice.
4. Default to parallel Explorer subagents for 2+ independent tracks. The user
   does not need to request subagents. Before reading a second track serially,
   run the Subagent Tool Discovery Gate from `dispatch-policy.md`; otherwise
   emit `Dispatch Exception:`.
5. Require Explorer Result Packet with observed/inferred/claimed evidence,
   confidence, dissent, open questions, and condensed evidence.
6. Read primary local evidence first and label key findings.
7. Use external calibration when current platform, dependency, model, API,
   upstream behavior, performance, unfamiliar frameworks, or repeated failures
   could affect the answer.
8. Synthesize options, preserve dissent, recommend the smallest producer-side
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

Return artifact path or none, question, dispatch packets or continuity
rationale, assumptions, evidence, options, recommendation, dissent, refresh
triggers, and `Route: teamwork-plan`.
