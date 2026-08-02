---
name: teamwork-explore
description: Use when a request or active workflow needs direct evidence about local code, files, configuration, logs, tests, history, artifacts, or runtime state as its result or next discriminator; do not use for external or current-source research, ordinary local reads already needed during implementation, unknown-cause diagnosis, design, or mutation.
---

# Teamwork Explore

Answer one bounded local evidence question. Explore is local-only and read-only:
it does not browse the web, edit files, run destructive commands, create a
standalone artifact, ask users directly, diagnose unknown causes, design, or
implement. The role mapping is exact: Explore -> Explorer. If Explorer is
unavailable or required isolation cannot be verified, return
`capability-blocked`; Root must not perform a named-method fallback.

## Method

1. State the precise local question and the decision or claim it affects. Resolve
   project root, instructions, canonical owner, control flow, tests/config, and
   invariants before scanning.
2. Use a healthy CodeGraph first for definitions, callers, impact, or flow. Use
   direct file, log, test, history, and runtime inspection for literal content or
   files the index reports stale. Avoid broad repository familiarization.
3. Prefer primary evidence: current source/configuration, the real command or
   test, runtime output, and version-control history. Treat summaries and
   generated copies as leads unless they are the named owner.
4. Separate observation from inference. Return one supported conclusion, the
   evidence that changes it, and at most one material gap or next discriminator.
5. Stop when answered or when the missing evidence is precisely identified.
   Explorer never asks the user. Return one exact local-evidence gap with its
   owner, scope, and resume condition to Root. If evidence reveals an unformed
   preference or material direction choice, return a reclassification signal to
   Collaborate; do not initiate that workflow.

Evidence belongs in the workflow packet or checkpoint that owns the decision.
Writer never creates an independent Explore artifact. Native fast path remains
outside Explore: tiny/discoverable local reads, ordinary explanations, simple
commands, integration, and reads needed for an already authorized change stay
with the active owner. If the remaining question is external/current, an
unknown-cause failure, an unsettled decision, or mutation, report that boundary.
