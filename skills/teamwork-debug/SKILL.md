---
name: teamwork-debug
description: Use when the user reports a failure, flaky test, CI error, runtime log, crash, UI symptom, regression, or suspected bug where a repro, hypotheses, instrumentation, browser/CI evidence, or human observation must decide root cause before a fix is safe.
---

# Teamwork Debug

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

Implement only a user-accepted confirming fix. Afterward, rerun the same repro
and remove temporary instrumentation without broadening cleanup.

## Done When

Return repro, hypotheses, instrumentation, runtime evidence, root cause or
bounded uncertainty, fix route, verification/cleanup, risk, and next route.

## Escalate

Route to research when evidence is insufficient, plan when accepted scope must
change, execute when scope is accepted, or apply the Ask Gate before blocking on
user-providable access, runtime values, or observation.

## Conditional Protocols

Use `debug-mode.md` for the diagnostic packet, `verification-patterns.md` for
baseline/treatment proof, `subagent-dispatch.md` and `subagent-contract.md` for
independent tracks, and `artifact-protocol.md` for durable findings. Paths are under
`skills/using-teamwork/references/`.
