---
name: teamwork-debug
description: Use when a failure, crash, flake, regression, or unexpected result has an unknown cause that blocks a safe fix.
---

# Teamwork Debug

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Remove only the uncertainty blocking the next safe fix. Debug is not a general
investigation, cleanup, or refactor stage.

## Enter When

Use when the cause cannot safely be inferred from the real failure. A supplied
error and clear narrow fix may execute directly. Stay in research when the
environment or repro surface is unknown; use Plan only when the fix changes a
protected public boundary.

## Do And Boundaries

Start from the actual failing command, environment, and first blocking error.
Gather only evidence that distinguishes the next possible fix; add temporary
instrumentation only when the existing failure cannot decide it. Never switch
targets or invent defaults to manufacture a repro. When the user already asked
for a fix and evidence supports a narrow change, implement it without an extra
confirmation cycle. Then rerun the same real path. Check adjacent behavior only
for a named shared/high-risk boundary, and remove temporary instrumentation.

## Done When

The real path works, or the remaining uncertainty is the specific blocker to the
next safe change. Stop when further diagnosis would not change that next action.

## Escalate

Route to research when evidence is insufficient, plan when accepted scope must
change, execute when scope is accepted, or apply the Ask Gate before blocking on
user-providable access, runtime values, or observation.

## Conditional Protocols

Under `skills/using-teamwork/references/`, use `debug-mode.md` for diagnosis,
`verification-patterns.md` for proof, delegation references for independent
tracks, and `artifact-protocol.md` for durable findings.
