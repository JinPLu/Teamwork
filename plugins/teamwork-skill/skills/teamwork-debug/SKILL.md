---
name: teamwork-debug
description: Use when a request or active workflow encounters a failure, crash, flake, regression, or unexpected result whose cause is still unknown and prevents a safe fix; do not use when the cause and narrow fix are already clear, for general fact finding or design, or when the user asks only for review.
---

# Teamwork Debug

Remove the uncertainty blocking the next safe fix, then prove the result on the
same real path. Debugging does not expand the requested scope.

Debug is a hypothesis-driven causal loop, not open-ended investigation,
Research, or Review. One invocation owns one frozen failure signature. Root and
every evidence role return to that same causal thread until it reaches a
terminal state. The role mapping is exact: Debug -> Debugger. If Debugger is
unavailable or required isolation cannot be verified, return
`capability-blocked`; Root must not perform a named-method fallback.

## Fixed Authority

Root dispatches one immutable authority for the diagnosis:

- `observe`: inspect and reproduce only;
- `instrument`: add and remove temporary diagnostic probes, but do not change
  product behavior;
- `fix`: diagnose, apply only the evidenced narrow fix, clean probes, and rerun.

Never infer or upgrade authority from a diagnosis, user answer, or promising fix.
If more authority is required, pause and return the exact blocked action.

## Freeze The Failure

Before diagnosis, freeze:

- the actual failing command, interaction, or runtime surface;
- environment and relevant immutable inputs;
- expected result, observed result, and first relevant error;
- the observable same-path success signal;
- protected boundaries and `observe`, `instrument`, or `fix` authority.

This is the failure signature. Do not silently replace it with a nearby test,
different dataset, local substitute, later error, or easier target. A materially
different failure signature is `new-failure-split`: return it as a separate
Debug case rather than pivoting the current diagnosis.

## Hypothesis Gate

When the cause is unknown, rank three to five plausible hypotheses before broad
inspection, instrumentation, external lookup, or repair. Do not pad the ledger
with implausible causes; if direct evidence already isolates one cause, state it
and proceed within authority instead of manufacturing alternatives.

Each hypothesis has a stable `H-*` ID and records:

- why it currently fits the failure;
- the observation predicted if it is true;
- the observation that would falsify it;
- the smallest deciding evidence;
- the different fix or next action it would imply.

Select one active discriminating experiment at a time. Before running it, state
which hypotheses each possible result supports or rejects. Every command, probe,
Explorer question, Research question, or human observation must name the active
`H-*` evidence gap. No hypothesis mapping means no probe.

### Runtime Log-First

For an unknown runtime, state, data-flow, event-flow, async, or UI failure under
`instrument` or `fix` authority, make the default active experiment a temporary
structured log at the nearest owned boundary. Give the experiment a stable
`E-*` ID, log only the fields needed to distinguish the leading hypotheses, and
preserve its raw result. Skip code instrumentation only when existing evidence already decides
a named `H-*` gap; state that evidence and the hypotheses it distinguishes.
Under `observe`, never add logs: use existing evidence or return `blocked` with
the exact missing discriminator.

After the observation, update the ledger exactly once: `supported`, `weakened`,
or `rejected`, with direct evidence. The live set must shrink, the causal
boundary must move, or the next experiment must change. Two consecutive
observations that do none of these are a no-progress stop: return `blocked`
with the missing discriminator instead of expanding the search.

## Causal Loop

1. Capture the actual failing command or interaction, environment, expected and
   observed result, and first relevant error. Reproduce when safe; do not swap in
   a synthetic target.
2. Apply the Hypothesis Gate. Freeze the ranked `H-*` ledger and select the
   active evidence gap before further inspection, instrumentation, or repair.
3. Trace from the failing boundary to the current owner only through that named
   `H-*` gap. Map every source/configuration/test/log/runtime inspection and
   command to it, then run the smallest observation that distinguishes the
   leaders. Treat summaries as leads, not proof, and change one variable at a
   time. For an eligible runtime failure under `instrument` or `fix` authority,
   use the Runtime Log-First experiment unless decisive existing evidence
   already distinguishes the named hypotheses; record any skip rationale. Load
   `references/runtime-diagnosis.md` only for that instrumented runtime path.
4. Update supported and rejected hypotheses. Confirm a cause only when the
   observation discriminates it from the remaining leaders and locates the
   first bad owned boundary. Correlation, a passing adjacent test, or absence of
   another error is not root-cause proof.
5. Under `observe` or `instrument`, stop at the evidenced cause and make no
   product change. Under `fix`, apply only the authorized narrow causal fix to
   the current owner. Avoid masking wrappers,
   silent fallbacks, broad cleanup, dependency upgrades, or unrelated refactors.
6. Remove temporary instrumentation and rerun the same failing path. Check an
   adjacent path only for named shared, public, security, data, or destructive-risk boundaries.

Use current external documentation only when an upstream version or platform
claim can distinguish a live hypothesis; cite that claim and keep the lookup
narrow. Never expose private project evidence in public search.

Root may dispatch one Debugger as the sole causal owner. Default to that one
child; daily work remains within cap4. Explorer or Researcher
may answer one named `H-*` evidence gap and must return evidence to that
Debugger; they do not open parallel investigations or own conclusions. Do not
invoke Reviewer, use `ACCEPT`/`REVISE`, or build acceptance gates while the
cause is unknown. Review may occur only after Debug has sealed a cause or fix
candidate and a user-requested or named material risk gate independently
requires it.

## Terminal States And Output

Use exactly one terminal state:

- `cause-confirmed`: direct evidence identifies the cause; no product change;
- `fix-verified`: the authorized narrow fix passes the original same path;
- `blocked`: the next discriminating evidence or authority is unavailable;
- `new-failure-split`: a different failure was found and must be diagnosed
  separately.

Return a compact Debug Findings packet:

```text
Debug Findings
- Status / Authority:
- Failure Signature:
- Expected / Observed / First Error:
- Ranked Hypotheses:
- Active Discriminating Experiment:
- Experiment Card / Instrumentation Decision:
- Raw Observation:
- Hypothesis Update:
- Evidence:
- Supported Cause:
- Rejected Hypotheses:
- Fix:
- Same-Path Verification:
- Probe Cleanup:
- New Failure Splits:
- Remaining Blocker / Next Action:
```

In an initialized writable project, terminal cause, blocked diagnosis, or
cross-session handoff defaults to a case-v2 debug artifact unless the user says `no
files`, `off-record`, `read-only`, `no writes`, or equivalent; it is not a turn
log. Freeze the bounded terminal or blocked packet before persistence. Debugger
returns a bounded packet: purpose/audience, facts/sources, frozen
decision/status, style/structure, artifact kind/consumer, preserve/forbid,
failure, cause evidence, attempted fixes, blocker, and verification. Writer
routes from observed schema: `case-inspect` first; case-v2 uses exact
`case_id`/alias or creates from a frozen seed/task_key, then
`case-schema <debug-add> -> case-apply -> case-inspect/readback`. The
transaction derives the destination and registers the case manifest/claim heads.
Writer is disposable; Root may
continue only answer-invariant delivery work and must join before claiming saved
or durable. Interruption before apply means unsaved unless surviving evidence
permits a new frozen packet. Missing project memory, Writer, brief, authority,
consumer, route, or transaction blocks only persistence: deliver the diagnosis
and report it unsaved/blocked. No Debugger, Root, or Worker fallback writes it.
Legacy-v1, mixed v1/v2, unknown, stale, ambiguous case, missing seed/task_key,
or partially migrated state fails closed before any write.

Ask only for the exact unavailable runtime value, access grant, or human-only
observation needed for the next discriminating check. Debugger or another leaf
proposes that blocker; Root presents it and the returned value resumes the same
diagnosis. Pause with the exact action and expected return value. A question or
diagnosis grants no new effect authority. If the safe fix would change accepted
behavior, contracts, data, permissions, or scope, stop and name that decision.

Finish with the cause and direct evidence, the exact fix if authorized, the real
rerun result, and any specific remaining blocker. The experiment card, raw
observation, hypothesis update, and probe cleanup are externally auditable work
state, never implicit reasoning. Stop as soon as the requested path works or no
safe evidence-backed next action remains.
