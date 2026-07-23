---
name: teamwork-debug
description: Use when a failure, crash, flake, regression, or unexpected result has an unknown cause that prevents a safe fix; do not use when the cause and narrow fix are already clear, for general fact finding or design, or when the user asks only for review.
---

# Teamwork Debug

Remove the uncertainty blocking the next safe fix, then prove the result on the
same real path. Debugging does not expand the requested scope.

## Fixed Authority

Root dispatches one immutable authority for the diagnosis:

- `observe`: inspect and reproduce only;
- `instrument`: add and remove temporary diagnostic probes, but do not change
  product behavior;
- `fix`: diagnose, apply only the evidenced narrow fix, clean probes, and rerun.

Never infer or upgrade authority from a diagnosis, user answer, or promising fix.
If more authority is required, pause and return the exact blocked action.

## Method

1. Capture the actual failing command or interaction, environment, expected and
   observed result, and first relevant error. Reproduce when safe; do not swap in
   a synthetic target.
2. Trace from failing boundary to current owner. Inspect local source,
   configuration, tests, logs, runtime state, and recent changes before asking.
   Treat summaries as leads, not proof.
3. List plausible hypotheses and select the smallest observation that
   distinguishes the leaders. Change one variable at a time. Add temporary
   instrumentation only under `instrument` or `fix` authority and only when
   current evidence cannot decide the next action. Load
   `references/runtime-diagnosis.md` only for that instrumented runtime path.
4. Under `observe` or `instrument`, stop at the evidenced cause and make no
   product change. Under `fix`, apply only the authorized narrow causal fix to
   the current owner. Avoid masking wrappers,
   silent fallbacks, broad cleanup, dependency upgrades, or unrelated refactors.
5. Remove temporary instrumentation and rerun the same failing path. Check an
   adjacent path only for named shared, public, security, data, or destructive-risk boundaries.

Use current external documentation only when an upstream version or platform
claim can distinguish a live hypothesis; cite that claim and keep the lookup
narrow. Never expose private project evidence in public search.

In an initialized writable project, terminal cause, blocked diagnosis, or
cross-session handoff defaults to a debug artifact unless the user says `no
files`, `off-record`, `read-only`, `no writes`, or equivalent; it is not a turn
log. Debugger returns a bounded packet: purpose/audience, facts/sources, frozen
decision/status, style/structure, artifact kind/consumer, preserve/forbid,
failure, cause evidence, attempted fixes, blocker, and verification. Writer uses
`artifact-inspect -> artifact-schema <create|update|supersede> -> artifact-apply`;
the transaction derives the destination and registers the ordinary index. Missing
project memory, Writer, brief, authority, consumer, or transaction blocks only
persistence: deliver the diagnosis and report it unsaved/blocked. No Debugger,
Root, or Worker fallback writes it.

Ask only for an unavailable runtime value, access grant, or human-only observation
needed for the next discriminating check. Pause with the exact action and expected
return value, then resume the same diagnosis. A question or diagnosis grants no
new effect authority. If the safe fix would change accepted behavior, contracts,
data, permissions, or scope, stop and name that decision.

Finish with the cause and direct evidence, the exact fix if authorized, the real
rerun result, and any specific remaining blocker. Stop as soon as the requested
path works or no safe evidence-backed next action remains.
