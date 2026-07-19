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

1. Capture the actual failing command or interaction, environment, expected
   result, observed result, and first relevant error. Reproduce it when safe and
   available; do not substitute a synthetic target merely because it is easier.
2. Trace from the failing boundary toward the current owner. Inspect local source,
   configuration, tests, logs, runtime state, and recent changes before asking
   the user. Treat summaries as leads, not proof.
3. List only plausible hypotheses and select the smallest observation that
   distinguishes the leading ones. Change one variable at a time. Add temporary
   instrumentation only under `instrument` or `fix` authority and only when
   existing evidence cannot decide the next action. Load
   `references/runtime-diagnosis.md` only for that instrumented runtime path.
4. Under `observe` or `instrument`, stop at the evidenced cause and make no
   product change. Under `fix`, apply only the authorized narrow causal fix to
   the current owner. Avoid masking wrappers,
   silent fallbacks, broad cleanup, dependency upgrades, or unrelated refactors.
5. Remove temporary instrumentation and rerun the same failing path. Check an
   adjacent path only when the change touches a named shared, public, security,
   data, or destructive-risk boundary.

Use current external documentation only when an upstream version or platform
claim can distinguish a live hypothesis; cite that claim and keep the lookup
narrow. Never expose private project evidence in public search.

Ask only for an unavailable runtime value, access grant, or human-only observation
required for the next discriminating check. Pause with the exact action and
expected return value, then resume the same diagnosis. A question or diagnosis
does not grant new effect authority. If the safe fix would change accepted behavior,
public contracts, data, permissions, or scope, stop and name that decision rather
than slipping it into the diagnosis.

Finish with the cause and direct evidence, the exact fix if authorized, the real
rerun result, and any specific remaining blocker. Stop as soon as the requested
path works or no safe evidence-backed next action remains.
