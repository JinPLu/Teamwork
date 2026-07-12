---
name: teamwork-review
description: Use when the user asks to review/check a plan, artifact, diff, implementation, research output, completion claim, strict quality, deslop pass, PR walkthrough, or acceptance evidence.
---

# Teamwork Review

## Outcome

Issue an independent, evidence-based `accept`, `revise`, or `blocked` verdict
for a plan, execution, or output. Review does not fix findings unless asked.

## Enter When

Use for requested review, acceptance, diff/output scrutiny, strict-quality
checks, PR walkthroughs, or risk-gated completion. Prefer fresh context for
high-risk, public-contract, delegated, security, destructive, release, or goal
acceptance; local self-review is sufficient for lightweight checks unless a
governing gate says otherwise.

## Do And Boundaries

Select `mode: plan`, `execution`, or `output`. Read primary sources directly:
constraints, plan, files, diff, artifacts, logs, tests, and command output.
Treat summaries and CI/test reports as inputs, not verdicts. Map each material
requirement to evidence and label important claims `observed`, `inferred`, or
`claimed`. For code, check owner/flow understanding, scope conformance,
tests/config, invariants, fallback masking, verification strength, delegated
packets, and touched-diff hygiene. Re-review must inspect the prior verdict,
requested fixes, and new evidence.

Classify findings as `blocker`, `major`, or `minor`; state the evidence and
required action. Never upgrade build-only, partial, or blocked proof into live
verification.

## Done When

Return mode, evidence read, requirements/evidence map, verification strength,
findings, dissent/uncertainty, verdict, and concise rationale. Acceptance
requires every gating requirement to pass or be explicitly out of scope.

## Escalate

Stop and return `blocked` when required evidence or access is missing; return
`revise` for correctable scope, quality, or proof failures.

## Conditional Protocols

Use `review-checks.md`, `verification-patterns.md`, and `review-lenses.md` for
the selected review. Load `debug-mode.md` or `goal-iteration.md` only for those
flows. Teamwork package, SkillOpt/HarnessOpt, ledger, and release rules are owned
by `eval-gate.md`; load them only when that gate applies. Paths are under
`skills/using-teamwork/references/`.
