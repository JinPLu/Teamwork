---
name: teamwork-debug
description: Use when something fails, crashes, flakes, regresses, or behaves unexpectedly and the cause must be reproduced and distinguished before a safe fix.
---

# Teamwork Debug

Read `skills/using-teamwork/references/workflow-contract.md` before proceeding.

## Outcome

Use runtime evidence to identify a supported root cause and the smallest safe
fix route. Debug is diagnosis, not a general cleanup or refactor stage.

## Enter When

Use for failures, crashes, CI errors, UI symptoms, regressions, or performance
problems unsafe to infer from source alone. Stay in research when the
environment or repro is unknown; route an accepted fix to execution, or an
architectural/public-contract fix to planning.

## Do And Boundaries

State expected versus actual behavior, the repro, acceptance signal, and
protected boundaries. Confirm commands, environment, paths, credentials,
models, and targets from user input or source/config; never switch targets or
invent defaults to manufacture a repro. Form only as many plausible hypotheses
as the evidence warrants and name discriminating evidence. Add minimal useful
instrumentation, reproduce, reject unsupported explanations, and state the
evidence-backed cause. Use human observation only when the agent cannot operate
the relevant session or UI; route that observation request through the root
under the Ask Gate in `workflow-contract.md`.

Implement only a user-accepted confirming fix. Afterward, rerun the evidence
needed to test the claimed fix and likely regressions, proportional to the
surface and risk, and remove temporary instrumentation without broadening cleanup.

## Done When

The observed failure and expected behavior are clear; evidence supports a root
cause or explicitly bounded uncertainty; temporary instrumentation is removed;
and the fix route, proof strength, remaining risk, and next route are truthful.

## Escalate

Route to research when evidence is insufficient, plan when accepted scope must
change, execute when scope is accepted, or apply the Ask Gate before blocking on
user-providable access, runtime values, or observation.

## Conditional Protocols

Under `skills/using-teamwork/references/`, use `debug-mode.md` for diagnosis,
`verification-patterns.md` for proof, delegation references for independent
tracks, and `artifact-protocol.md` for durable findings.
