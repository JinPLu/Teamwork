---
name: teamwork-research
description: Use when the next step is evidence gathering, root-cause investigation, option comparison, external research, or refreshing stale assumptions — especially before planning any non-trivial change. Invoke even when you think you already know the answer; verify first.
---

# Teamwork Research

Use this subskill when the next step is evidence gathering, option comparison,
root-cause investigation, external research, or refreshing stale assumptions.
Research first establishes the local project reality and mainline from direct
evidence, then uses external calibration to avoid local trial-and-error loops.
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

- Start with local files, diffs, logs, tests, artifacts, and prior research
  artifacts to understand the actual project state, active code paths, current
  progress, and mainline constraints.
- For non-trivial research, add external calibration instead of treating it as a
  last-resort fallback. Use web, GitHub issues, official docs, release notes,
  papers, or MCP-backed sources when model/prompt work, VLM/video
  understanding, platform APIs, CLI behavior, third-party libraries,
  version-sensitive errors, upstream bugs, performance, unfamiliar frameworks,
  or repeated failures could affect the answer.
- Prefer official docs, primary issue threads, papers, release notes, and other
  primary sources. If web, MCP, credentials, or network access is unavailable,
  record that limitation in the artifact and clearly mark external evidence as
  missing rather than silently relying on local guesses.
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

Before starting new research, search existing `docs/teamwork/research/`
artifacts for the same topic. Reuse, update, or explicitly cite the existing
artifact when it remains applicable; create a new artifact when the topic,
evidence, or recommendation has materially changed. Research artifacts are
working memory: maintain them so later planning, execution, review, and goal
iterations do not repeat the same searches.

## Workflow

1. Define the research question and success criteria.
2. Search existing research artifacts for reusable evidence, stale assumptions,
   or prior recommendations on the same topic.
3. Split the topic into independent tracks when useful: project mainline,
   symptoms, source paths, artifacts, external constraints, alternative designs,
   upstream reports, papers, or current best practices.
4. Assign each useful track a role or pass. Each pass reads primary evidence
   directly and returns findings, confidence, and open questions.
5. Search external sources for non-trivial work where outside behavior,
   prior art, or current field practice could prevent local dead-end attempts.
6. Generate options before committing. Prefer simple, local, producer-side
   fixes over broad rewrites or downstream cleanup.
7. Compare options against the goal, sacred boundaries, verification path, and
   budget.
8. Preserve dissent. Label minority findings as blocker, warning, or follow-up.
9. Write or update the research artifact at `docs/teamwork/research/YYYY-MM-DD-<slug>.md`
   using the Write tool. Do this before outputting the handoff block. Confirm
   the file exists at the expected path.
10. Stop when a direction is selected, evidence is insufficient, budget is
   exhausted, or only protected/ambiguous decisions remain.

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

## Research Refresh Triggers

During execution or goal iteration, route back to `teamwork-research` when:

- verification produces no evidence delta after a focused fix;
- one focused fix or prompt change has already produced no evidence delta and
  the next move would otherwise be another local guess;
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
