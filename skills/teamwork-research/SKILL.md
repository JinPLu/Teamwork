---
name: teamwork-research
description: Use when the next step is evidence gathering, root-cause investigation, option comparison, external calibration, stale-assumption refresh, or failure analysis before planning.
---

# Teamwork Research

Research establishes project reality from direct evidence, adds external
calibration when useful, compares options, and hands a selected direction to
`teamwork-plan`. It does not produce executable implementation plans.

Read first:

- `skills/teamwork/references/workflow-contract.md` for the Evidence Interpretation Contract and Context & Cost Discipline.
- `skills/teamwork/references/artifact-protocol.md` for full-text research retrieval, artifact triggers, and reuse/update/new decisions.
- `skills/teamwork/references/goal-iteration.md` only for goal-mode failure
  analysis.

## Research Artifact Requirement

Write or update a research artifact when findings will be reused, feed a
durable plan, support goal-mode iteration or failure analysis, use external
calibration, refresh assumptions after repeated failure, or justify a
non-trivial recommendation:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
```

For a lightweight one-turn lookup, cite evidence in the response instead.

Before new non-trivial research, Search existing research artifacts with goal
words, exact errors, component paths, model/API/dependency names, external
entities, and old artifact slugs. Choose one disposition: reuse, update, or new.

## Workflow

1. Define the research question and success criteria.
2. Retrieve prior research and record the reuse/update/new disposition.
3. Split separable evidence questions into tracks such as local mainline,
   symptoms, source paths, artifacts, external constraints, alternatives,
   upstream reports, papers, or current best practices.
4. Prefer parallel Explorer subagents when 2 or more tracks can run without
   blocking the next local step; otherwise keep the pass local.
5. Read primary local evidence first. Label important findings as `observed`,
   `inferred`, or `claimed`.
6. Use external calibration for non-trivial work where platform, dependency,
   model, prompt, upstream, performance, unfamiliar frameworks, or repeated
   failures could affect the answer.
7. Generate options before recommending. Prefer simple producer-side fixes over
   rewrites or downstream cleanup.
8. Preserve dissent and unresolved risks.
9. Write/update the artifact when required and confirm it exists before an
   artifact-backed handoff.
10. Stop when a direction is selected, evidence is insufficient, budget is
    exhausted, or a protected/ambiguous decision remains.

## Research Refresh Triggers

Route back to research when:

- verification produces no evidence delta after a focused fix;
- one focused fix or prompt change already produced no evidence delta;
- goal execution cannot be accepted until the current plan is checked against
  failure evidence;
- reviewer dissent says the executor is reinforcing the same assumption;
- the issue may be upstream, version-specific, environment-specific, or already
  discussed in primary sources;
- local evidence contradicts docs, names, comments, or prior summaries;
- implementation is becoming broader without new evidence;
- the active plan is invalidated by new facts.

## Research Artifact Template

```text
# <Topic> Research

## Research Question
## Local Evidence
## External Evidence
## Prior Research Reused
## Options
## Recommendation
## Dissent / Unresolved
## Refresh Triggers
```

## Handoff to Plan

```text
Mode:
- research

Research Artifact:
- docs/teamwork/research/YYYY-MM-DD-<slug>.md | none

Research Question:
- ...

Assumptions:
- ...

Local Evidence:
- <observed|inferred|claimed> <path/command/artifact>: <finding>

External Evidence:
- <observed|inferred|claimed> <url/source>: <finding or unavailable because ...>

Options:
1. <option> - benefit, risk, verification, boundary impact

Recommendation:
- <selected direction or blocked>
- Why this is the simplest sufficient path

Dissent / Unresolved:
- ...

Refresh Triggers:
- ...

Plan Handoff:
- Route: teamwork-plan
- Research artifact: <path | none>
```
