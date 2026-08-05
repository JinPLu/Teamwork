---
name: teamwork-debug
description: Use when a failure, crash, flake, regression, or unexpected result has an unknown cause and must be diagnosed before a safe fix; do not use when the cause and narrow fix are already clear, to review a finished candidate, or for general research.
---

# Teamwork Debug

Use Debugger as the causal owner. Hold one failure signature and follow evidence
until the cause is confirmed, the authorized fix is verified, or the next
discriminator is unavailable. Do not widen the requested scope.

## Establish The Boundary

Capture the actual failing command or interaction, environment and relevant
inputs, expected result, observed result, first relevant error, and the same-path
success signal. Do not substitute an easier target. Treat a materially different
failure as `new-failure-split`.

Derive the operating mode from the user request and host/tool authority:

- `observe`: inspect and reproduce without changing files or behavior;
- `instrument`: add reversible diagnostic probes, then remove them;
- `fix`: diagnose, apply the evidenced narrow fix, clean probes, and rerun.

Never elevate the mode implicitly. If the next discriminating action is outside
the available authority, return its exact requirement as the blocker.

## Hypothesis Loop

1. Rank three to five plausible `H-*` hypotheses before broad inspection or
   repair. Do not pad the set; if direct evidence already isolates one cause,
   state that evidence and continue without invented alternatives.
2. For each hypothesis, record why it fits, its predicted observation, what
   would falsify it, the smallest deciding evidence, and the distinct action it
   implies.
3. Select one discriminating `E-*` experiment. Before running it, state how each
   possible result changes the leading hypotheses. Map every inspection, probe,
   lookup, or human observation to that evidence gap.
4. Preserve the raw observation, then update each affected hypothesis to
   `supported`, `weakened`, or `rejected`. The live set must shrink, the causal
   boundary must move, or the next experiment must change. Otherwise stop and
   name the missing discriminator instead of expanding the search.
5. Confirm a cause only when evidence distinguishes it from the remaining
   leaders and locates the first bad owned boundary. Correlation, an adjacent
   passing test, or disappearance of a later error is not causal proof.
6. Under `observe` or `instrument`, stop at the supported cause. Under `fix`,
   make only the narrow causal correction, remove probes, and rerun the original
   path. Check adjacent behavior only where a named shared or high-risk boundary
   requires it.

Use Explorer or Researcher only to answer a named `H-*` evidence gap and return
the result to Debugger. Do not open parallel causal owners. Load
`references/runtime-diagnosis.md` when a runtime, state, data-flow, event-flow,
async, or UI hypothesis needs temporary instrumentation. Structured logging is
one optional probe, not the default for every runtime failure.

## Terminal Result

Use one terminal state:

- `cause-confirmed`: direct evidence identifies the cause; no product change;
- `fix-verified`: the narrow fix passes the original path;
- `blocked`: the next discriminator, input, access, or authority is unavailable;
- `new-failure-split`: a materially different failure needs its own diagnosis.

Report the failure signature, operating mode, ranked hypotheses, active
experiment, raw observation, hypothesis update, supported cause, rejected
hypotheses, fix if any, same-path rerun, probe cleanup, and exact remaining
blocker or next action.

## Live Document

Have Writer maintain the task's single live document with a debug shape; reuse
it rather than creating a parallel artifact. Create it when the first reusable
failure signature or discriminating result appears, update it only when a
hypothesis, observation, cause, fix, verification, blocker, or next experiment
materially changes, and finalize it at a terminal state. Include the
failure signature, hypotheses, experiment cards, raw observations, evidence,
cause, fix, verification, cleanup, and status. Writer must not reinterpret the
evidence or promote a hypothesis to a confirmed cause.
