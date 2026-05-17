---
name: teamwork-research
description: Use when the next step is evidence gathering, root-cause investigation, option comparison, external research, or refreshing stale assumptions — especially before planning any non-trivial change. Invoke even when you think you already know the answer; verify first.
---

# Teamwork Research

Use this subskill when the next step is evidence gathering, option comparison,
root-cause investigation, external research, or refreshing stale assumptions.
Research may recommend a direction, but executable implementation planning
belongs to `teamwork-plan`.

## Shared Inputs

- Goal, failure, or decision to resolve.
- Known evidence: command output, logs, artifacts, diffs, source locations.
- Sacred boundaries: principles, contracts, architecture, user constraints.
- Mutable scope: exact areas that may change.
- Verification target: command, artifact, metric, or acceptance criteria.
- Budget and stop rules.

State missing inputs as assumptions before they affect behavior. If an
assumption would change public behavior, protected claims, data contracts, or
architecture, stop and ask instead of guessing. In `teamwork-goal`
`mode: goal`, safe internal details should become explicit assumptions rather
than user questions.

## Evidence Interpretation Contract

Treat file names, directory names, version labels such as `v2`, `latest`,
comments, README prose, historical notes, and prior summaries as claims, not
facts. Before using them to choose a direction, corroborate them with direct
evidence such as source call paths, tests, configuration, command output,
artifact properties, or git diff.

Label important findings as:

- `observed`: direct evidence you inspected.
- `inferred`: a conclusion drawn from observed evidence.
- `claimed`: narrative, naming, or documentation text that still needs
  corroboration.

Do not let a claimed label decide scope, canonical files, version freshness, or
completion status without at least one direct evidence cross-check.

## Context & Cost Discipline

- Prefer local files, diffs, logs, tests, and artifacts before MCP or web when
  local evidence can answer the question.
- Use web, GitHub issues, official docs, release notes, or MCP-backed sources
  when current external behavior may affect the answer: platform APIs, CLI
  behavior, third-party libraries, version-sensitive errors, upstream bugs, or
  unfamiliar framework constraints. Prefer official docs and primary issue
  threads. If web or MCP access is unavailable, record that limitation in the
  artifact.
- Fan out subagents only after splitting the research into independent tracks
  that can run in parallel without blocking the main agent's immediate next
  step. Each track needs a specific question, evidence scope, return format, and
  confidence/dissent request.
- Ask subagents to return condensed evidence, confidence, dissent, and open
  questions instead of large raw logs.
- Default research fan-out is at most 3 parallel subagents unless the user gives
  a larger budget. Do not fan out when one local pass can answer the question
  faster or when the tracks would duplicate the same evidence.

## Research Artifact Requirement

Always write a durable research artifact to disk before handing off to planning
or reporting completion:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
```

Use the Write tool to create the file. The only exception is a single direct
lookup whose entire finding fits in one line and no later plan, execution,
review, or goal iteration will need it. If in doubt, write the artifact.

Do not output the handoff block until the file exists at the expected path.

## Workflow

1. Define the research question and success criteria.
2. Split the topic into independent tracks when useful: symptoms, source paths,
   artifacts, external constraints, alternative designs, upstream reports.
3. Assign each useful track a role or pass. Each pass reads primary evidence
   directly and returns findings, confidence, and open questions.
4. Search external sources when current platform behavior, upstream bugs,
   version-sensitive APIs, or unfamiliar ecosystem constraints could matter.
5. Generate options before committing. Prefer simple, local, producer-side
   fixes over broad rewrites or downstream cleanup.
6. Compare options against the goal, sacred boundaries, verification path, and
   budget.
7. Preserve dissent. Label minority findings as blocker, warning, or follow-up.
8. Write the research artifact to `docs/teamwork/research/YYYY-MM-DD-<slug>.md`
   using the Write tool. Do this before outputting the handoff block. Confirm
   the file exists at the expected path.
9. Stop when a direction is selected, evidence is insufficient, budget is
   exhausted, or only protected/ambiguous decisions remain.

## Research Artifact Template

```text
# <Topic> Research

## Research Question

## Local Evidence

## External Evidence

## Options

## Recommendation

## Dissent / Unresolved

## Refresh Triggers
```

## Research Refresh Triggers

During execution or goal iteration, route back to `teamwork-research` when:

- verification produces no evidence delta after a focused fix;
- reviewer dissent says the executor is reinforcing the same assumption;
- the error may be upstream, version-specific, environment-specific, or already
  discussed in GitHub issues;
- local evidence contradicts docs, names, comments, or prior summaries;
- the implementation is becoming broader or more complex without new evidence;
- the active plan is invalidated by new facts.

## Handoff to Plan

After selecting a direction, route to `teamwork-plan`. Provide the research
artifact path, recommended direction, preserved dissent, and refresh triggers.

Output:

```text
Mode:
- research

Research Artifact:
- docs/teamwork/research/YYYY-MM-DD-<slug>.md

Research Question:
- ...

Assumptions:
- ...

Local Evidence:
- <observed|inferred|claimed> <path/command/artifact>: <finding>

External Evidence:
- <observed|inferred|claimed> <url/source>: <finding or unavailable because ...>

Options:
1. <option> - benefits, risks, verification, boundary impact
2. ...

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
