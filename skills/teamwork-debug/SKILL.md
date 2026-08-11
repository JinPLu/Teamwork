---
name: teamwork-debug
description: Use when a failure, crash, flake, regression, or unexpected result has an unknown cause and must be diagnosed before a safe fix; do not use when the cause and narrow fix are already clear, to review a stable candidate, or for general research.
---

# Teamwork Debug

Debug is the current causal stage. Debugger owns one failure investigation;
Root owns user communication, authority, and any stage switch. Follow evidence
until the cause is supported, an authorized fix passes the original path, the
next discriminator is unavailable, or a materially different failure appears.

## Bound The Failure

Capture the actual failing command or interaction, relevant environment and
inputs, expected and observed results, first useful error or divergence, and
the same-path success signal. Do not substitute an easier target.

Derive the operating boundary from the request and current authority:

- observe: inspect and reproduce without changing files or behavior;
- instrument: add reversible diagnostic probes and remove them afterward;
- fix: diagnose, apply only the evidenced correction, clean probes, and rerun.

Do not elevate authority implicitly. A materially different signature becomes
`new-failure-split`; it is not silently folded into the current diagnosis.

## Causal Loop

1. Form only the hypotheses justified by current evidence. One strong
   hypothesis is enough when direct evidence isolates it; several are useful
   only when they remain genuinely plausible and imply different observations.
2. For each live hypothesis, identify why it fits, what would distinguish or
   weaken it, and what different next action would follow.
3. Choose the smallest observation or experiment that best separates the live
   alternatives. State how its possible outcomes change the causal picture,
   then preserve the actual observation.
4. Update the hypothesis standing and causal boundary. If the evidence neither
   narrows the cause nor changes the next discriminator, stop and name the
   missing evidence instead of expanding mechanically.
5. Confirm a cause only when evidence distinguishes it from credible
   alternatives and locates the first bad owned boundary. Correlation, a nearby
   passing check, or disappearance of a downstream error is not enough.
6. In fix authority, apply the narrow causal correction, remove temporary
   probes, and rerun the original path. Check adjacent behavior only when a
   demonstrated shared boundary makes it relevant.

Read `references/runtime-diagnosis.md` when runtime, state, data-flow,
event-flow, asynchronous, or UI behavior needs temporary instrumentation.
Explorer or Researcher may answer an independently bounded evidence question
and returns it to Debugger; neither becomes another causal owner or creates a
separate document.

Debugger is required. Root must not imitate it when unavailable. Suspend Debug,
switch to Update for readiness repair, wait, and resume or return the exact
blocker.

## Codex Role Dispatch

On Codex, dispatch Debugger, Explorer, Researcher, and Writer through
`spawn_agent.agent_type` as `teamwork_debugger`, `teamwork_explorer`,
`teamwork_researcher`, and `teamwork_writer`. Use `fork_turns` set to `none`
or a bounded recent context, then observe a live child start; never silently
substitute an unavailable role.

When context is omitted or bounded, the brief must include every still-applicable
settled user constraint. A child cannot infer that a missing constraint was relaxed.

## Result And Debug Document

Use the semantic state that follows from the evidence: `cause-confirmed`,
`fix-verified`, `blocked`, or `new-failure-split`. Report the causal picture,
decisive observations, supported cause or next discriminator, authorized fix
and same-path verification when applicable, probe cleanup, and remaining action
without forcing a fixed packet.

When a bounded failure plus a real hypothesis or direct causal evidence becomes
reusable, Root assigns Writer the typed Debug document. Update it only when the
failure boundary, hypothesis standing, discriminator, cause, fix, or
verification materially changes. Writer may not promote a hypothesis to a
cause. Same-scope editorial corrections may update a finalized document;
materially new failure scope needs a new Debug document.
