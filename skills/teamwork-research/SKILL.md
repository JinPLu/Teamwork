---
name: teamwork-research
description: Use when the next safe step is to learn before acting: source-of-truth lookup, current API behavior, repro-surface framing, option comparison, stale-assumption refresh, or risk/evidence gathering before planning/debugging.
---

# Teamwork Research

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Establish project reality and return an evidence-backed answer, comparison,
debug route, or plan-ready recommendation without implementing the change.

## Enter When

Use when source of truth, current behavior, repro surface, alternatives, or risk
is unclear. Treat a supplied article, URL, paper, repo, or report as seed
evidence, not the research boundary. Route reproducible runtime failures to
`teamwork-debug`. Do not enter merely to explain supplied facts when no lookup
or stale-assumption check is needed; return to Native.

## Do And Boundaries

Define the question and decision signal, check relevant prior artifacts, then
split independent evidence tracks only when fan-out has clear value. Read local
primary evidence first. Use current external sources when an API, dependency,
model, platform, method, or upstream behavior may have changed; never send
private source to public search. Distinguish important `observed`, `inferred`,
and `claimed` findings, preserve meaningful dissent, and cite the evidence that
supports the conclusion. Research does not authorize edits, external writes,
or invented runtime values.

Write `docs/teamwork/research/YYYY-MM-DD-<slug>.md` only when findings need
cross-turn reuse, support a durable plan or goal, or justify a consequential
decision. External calibration alone does not require an artifact.

## Done When

The decision-relevant sources are covered, observations and inferences are
distinguished where material, and the answer states supported conclusions,
remaining uncertainty, and the appropriate next route. A durable artifact
exists only when its trigger applies.

## Escalate

Apply the Ask Gate in `workflow-contract.md` when research needs user-supplied
evidence or a user-owned decision. Stop when required evidence or access is
unavailable.

## Conditional Protocols

Use `research-protocol.md` for lookup/deep research, `subagent-dispatch.md` and
`subagent-contract.md` for fan-out, `artifact-protocol.md` for durable findings,
and `optional-skills.md` for external tools. All paths are under
`skills/using-teamwork/references/`.
