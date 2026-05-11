---
name: run-analyze-research
description: >-
  Use for multi-agent research, discussion, option generation, and divergent
  exploration before committing to a plan in a run-analyze-optimize workflow.
disable-model-invocation: true
---

# Run-Analyze Research

Use this subskill when the next step is unclear, the problem has multiple
plausible causes, or option generation is useful before selecting a direction.
Do not use it to implement changes.

## Inputs

- Goal or failure to understand.
- Known evidence: command output, logs, artifacts, diffs, source locations.
- Sacred boundaries: principles, contracts, architecture, user constraints.
- Budget: time, iteration count, model/cost ceiling, or stop signal.

State missing inputs as assumptions before starting.

## Workflow

1. Define the research question and success criteria.
2. Split the topic into independent tracks when possible: symptoms, source
   paths, artifacts, external constraints, alternative designs.
3. Assign each track a role or pass. Each pass reads primary evidence directly
   and returns findings, confidence, and open questions.
4. Generate options before committing. Prefer simple, local, producer-side fixes
   over broad rewrites or downstream cleanup.
5. Compare options against the goal, sacred boundaries, verification path, and
   budget.
6. Preserve dissent. Do not erase minority findings; label whether they block,
   warn, or merely need follow-up.
7. Stop when a direction is selected, evidence is insufficient, budget is
   exhausted, or only sacred/ambiguous decisions remain.

## Evidence Rules

- Evidence first: read logs, artifacts, diffs, and relevant source before
  explaining causes.
- Distinguish observation from inference.
- Prefer independent reads over summaries from another agent.
- Record contradictions and resolve them with source evidence when possible.
- Do not invent numbers, paths, APIs, or success criteria.

## Output Format

```text
Research Question:
- ...

Assumptions:
- ...

Evidence Read:
- <path/command/artifact>: <finding>

Options:
1. <option> - benefits, risks, verification, boundary impact
2. ...

Dissent / Unresolved:
- ...

Recommendation:
- <selected direction or blocked>
- Why this is the simplest sufficient path
```
