---
name: teamwork-research
description: Use when the next safe step is to learn before acting: source-of-truth lookup, current API behavior, repro-surface framing, option comparison, stale-assumption refresh, or risk/evidence gathering before planning/debugging.
---

# Teamwork Research

## Outcome

Establish project reality and return an evidence-backed answer, comparison,
debug route, or plan-ready recommendation without implementing the change.

## Enter When

Use when source of truth, current behavior, repro surface, alternatives, or risk
is unclear. Treat a supplied article, URL, paper, repo, or report as seed
evidence, not the research boundary. Route reproducible runtime failures to
`teamwork-debug`; skip research only when direct evidence already resolves the
uncertainty.

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

Return the question, evidence or verification, assumptions, options when
relevant, recommendation, dissent or gaps, artifact path or `none`, and one route:
`teamwork-debug`, `teamwork-plan`, follow-up research, or none.

## Escalate

Ask for a user-owned decision when remaining uncertainty changes scope or risk;
stop when required evidence or access is unavailable.

## Conditional Protocols

Use `research-protocol.md` for lookup/deep research, `subagent-dispatch.md` and
`subagent-contract.md` for fan-out, `artifact-protocol.md` for durable findings,
and `optional-skills.md` for external tools. All paths are under
`skills/using-teamwork/references/`.
