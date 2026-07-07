---
name: teamwork-debug
description: Use when the user reports a failure, flaky test, CI error, runtime log, crash, UI symptom, regression, or suspected bug where a repro, hypotheses, instrumentation, browser/CI evidence, or human observation must decide root cause before a fix is safe.
---

# Teamwork Debug

Use when a failure is real but the cause is unclear, and runtime evidence could
decide the next safe change. Debug is a diagnosis stage, not a new role and not
a general cleanup/refactor pass.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence and no-silent-default rules; `skills/using-teamwork/references/debug-mode.md`
for the debug loop; `skills/using-teamwork/references/verification-patterns.md`
for baseline/treatment proof and verification strength; `skills/using-teamwork/references/subagent-dispatch.md` and
`skills/using-teamwork/references/subagent-contract.md` for Explorer/Worker
packets; `skills/using-teamwork/references/artifact-protocol.md` for durable
findings; `skills/using-teamwork/references/optional-skills.md` before external
browser, CI, logging, or observability tools.

## When To Use

Route here when the user describes a failure symptom, failing/flaky command, CI
error, crash, runtime log, browser/UI bug, regression, timing issue, or
memory/performance failure where source inspection alone is guessing.

Stay in `teamwork-research` when the repro surface, source of truth, upstream
behavior, or environment is still unknown. Route to `teamwork-plan` when the
root cause is known but the fix changes architecture, public behavior, data
contracts, or protected boundaries. Route to `teamwork-execute` when an accepted
plan or already accepted scope only needs a targeted fix.

## Preconditions

- Expected vs actual behavior can be stated, or the first task is to make it
  explicit.
- A repro path exists or can be attempted: command, test, browser flow, CI log,
  trace, or human-in-loop action.
- Required runtime values, paths, env, commands, credentials, ports, models, and
  execution targets are explicit or discoverable from source/config.

Ask or block before inventing missing runtime targets. Do not switch local/remote,
dev/prod, browser/session, dataset, model, CI target, or path alias to hide a
missing invariant or make the bug easier.

## Workflow

1. Define expected/actual behavior, repro path, acceptance signal, and protected
   boundaries.
2. Rank 3-5 hypotheses and name the evidence that would confirm or reject each.
3. Choose minimal instrumentation: temporary logs/probes, browser/console/network
   capture, CI/log inspection, trace output, or manual observations.
4. Reproduce. Prefer agent-run repro when deterministic and toolable; use
   human-in-loop repro only for session/UI/manual state the agent cannot operate.
5. Analyze runtime evidence, reject hypotheses, and state the supported root
   cause.
6. Route: `research` if evidence is insufficient, `plan` if fix scope changes,
   `execute` if the fix scope is accepted, or `blocked` for missing resources.
   Debug may run only a tiny confirming fix when the user already accepted that
   scope; otherwise hand off before implementation.
7. After an executed fix, verify with the repro and remove temporary
   instrumentation.

## Cleanup And Quality

Debug cleanup removes temporary instrumentation, debug logs, scaffolding, and
obvious touched-diff slop while preserving behavior. Do not broaden cleanup into
structural refactors or fallback masking; route strict maintainability concerns
to `teamwork-review`.

## Output

Return a Debug Findings packet from `debug-mode.md`: repro, hypotheses,
instrumentation, runtime evidence, root cause, fix route, verification, cleanup
evidence, residual risk, and next route. Include `Memory Delta:` only when
durable project memory was checked or changed.
