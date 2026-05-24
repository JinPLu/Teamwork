---
name: teamwork-research
description: Use when the next step is evidence gathering, root-cause investigation, option comparison, external calibration, stale-assumption refresh, or failure analysis before planning.
---

# Teamwork Research

Research establishes project reality from direct evidence, adds external
calibration when useful, compares options, and hands a selected direction to
`teamwork-plan`. It does not produce executable implementation plans.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence and
  context discipline.
- `skills/using-teamwork/references/artifact-protocol.md` for artifact
  triggers, retrieval, templates, and reuse/update/new decisions.
- `skills/using-teamwork/references/goal-iteration.md` for goal-mode failure
  analysis.

## Research Artifact Requirement

Write or update `docs/teamwork/research/YYYY-MM-DD-<slug>.md` when findings
will be reused, feed a durable plan, support goal-mode iteration, use external
calibration, refresh failed assumptions, or justify a non-trivial
recommendation. For lightweight one-turn lookup, cite evidence in chat.

Search existing research artifacts before new non-trivial research with goal
words, exact errors, paths, model/API/dependency names, external entities, and
old slugs. Use the Retrieval Header fields including Search Keys and Abstract.
Choose one disposition: reuse, update, or new.

## Workflow

1. Define the research question and success criteria.
2. Retrieve prior research and record disposition.
3. Split separable evidence questions into tracks such as local source,
   symptoms, artifacts, external constraints, alternatives, upstream reports,
   papers, or current best practices.
4. Default to parallel Explorer subagents when 2+ tracks can run independently;
   otherwise state why local research is cheaper or safer.
5. Read primary local evidence first; label key findings `observed`,
   `inferred`, or `claimed`.
6. Use external calibration when current platform, dependency, model, API,
   upstream behavior, performance, unfamiliar frameworks, or repeated failures
   could affect the answer.
7. Generate options before recommending; prefer simple producer-side fixes.
8. Preserve dissent, risks, and protected/ambiguous decisions.
9. Write/update required artifact and confirm it exists before handoff.

## Research Refresh Triggers

Route back to research when verification has no evidence delta, reviewer
dissent says the same assumption is reinforced, the issue may be
version/environment/upstream-specific, local evidence contradicts claims,
implementation broadens without evidence, or the active plan is invalidated.

## Handoff

Return mode, research artifact path or none, question, assumptions, local and
external evidence, options, recommendation, dissent, refresh triggers, and
`Route: teamwork-plan`.
