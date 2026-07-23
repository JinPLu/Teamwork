---
name: teamwork-explore
description: Use when the requested result is direct evidence about local code, files, configuration, logs, tests, history, artifacts, or runtime state; do not use for external or current-source research, ordinary local reads needed during implementation, unknown-cause diagnosis, design, or mutation.
---

# Teamwork Explore

Answer one local evidence question without changing the project. Explore is
local-only and read-only; it does not browse the web, edit files, run destructive
commands, or turn an investigation into implementation.

## Method

1. State the precise local question and the decision or claim it affects. Resolve
   the project root, applicable instructions, and canonical owner before scanning.
2. Use a healthy CodeGraph first for structural questions such as definitions,
   callers, impact, or flow. Use direct file, log, test, history, and runtime
   inspection for literal content or when the index reports the relevant file as
   stale. Do not broadly “familiarize” yourself with the repository.
3. Prefer the nearest primary evidence: current source and configuration, the
   real test or command, runtime output, and version-control history. Treat
   summaries and generated copies as leads unless they are the named owner.
4. Separate observation from inference. Give one supported conclusion, the
   evidence that changes it, and at most one material gap or next discriminator.
5. Stop when the local question is answered or the missing evidence is precisely
   identified. Do not create an Explore report; evidence belongs in the workflow
   writing brief, packet, or artifact that owns the decision. Writer never
   creates an independent Explore artifact.

Use Explore when the evidence question is structurally complex (multiple files,
callers, definitions, or history), separable from the current task, or benefits
from CodeGraph-first inspection. Ordinary single-file reads, configuration lookups,
and reads that enable an already-scoped authorized change stay native.

Ordinary focused reads performed to complete an already authorized change do not
activate Explore. If the remaining question is external/current, unknown-cause
runtime diagnosis, an unsettled design choice, or a requested mutation, report
that boundary without performing the other work.
