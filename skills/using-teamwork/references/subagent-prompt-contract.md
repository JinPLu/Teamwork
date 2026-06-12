# Subagent Prompt Contract

Use for delegated prompts. Native flow summarizes. For dispatch read
`dispatch-policy.md`; for native fields read `platform-dispatch-mapping.md`;
for returned shapes read `subagent-packets.md`.

## Context Strategies

- `condensed-evidence-only`: question, paths, commands, budget, and expected packet.
- `artifact-backed`: durable artifact paths plus required sections.
- `owned-files-only`: owned paths, allowed edits, and verification target.
- `fresh-context-review`: review target, criteria, diff/artifacts, rejection
  rules, and no parent reasoning.
- `full-history-fork`: side task needs nearly all parent context. Codex uses
  `fork_context:true`; Cursor uses `resume:"self"`; Claude passes condensed context.
- `explicit-non-inheriting-dispatch`: role, model tier, or reasoning differs.
  Override Codex `agent_type`/model/reasoning, Cursor `subagent_type`/model, or
  Claude `subagent_type`.

## Required Fields

Delegated prompts include:

- Conceptual Role: Explorer, Designer, Judge, Worker, or Reviewer. Deep Judge
  and Deep Reviewer are severity profiles, not roles.
- Native Fields: fields from `platform-dispatch-mapping.md` plus model class. Codex
  role dispatch uses `agent_type`, model/reasoning, and `fork_context:false`;
  full-history fork (`fork_context:true`, inherited model, no
  `agent_type/model/reasoning_effort`). Cursor uses `subagent_type`, `model` or inherited.
- Mission: one question, decision, slice, or review.
- Source: plan, research, report, diff, output, or paths.
- Inputs: files, commands, evidence, assumptions, required values, target.
- Owned Scope: files/components the subagent may inspect or edit.
- Allowed Actions: read-only, workspace-write, verification, review-only.
- Forbidden Actions: scope expansion, destructive operations, credentials,
  overlapping writes, unrelated cleanup, broad refactors, final acceptance,
  follow-on monitoring, chaining subagents, or continuing after the packet.
- Context Strategy: one value from `Context Strategies`.
- Verification Target: command/artifact/behavior/checklist.
- Escalation Triggers: missing context, missing required env/path/command/model/config
  values, unclear ownership, protected boundary, plan mismatch, destructive risk, auth failure, or
  uncertainty changing intent, acceptance, public behavior, architecture, or
  contracts. Subagents report questions; the orchestrator asks the user.
- Required Output Schema: packet from `subagent-packets.md`.
- Closure Instruction: return packet once, then stop; the
  orchestrator owns integration, final acceptance, and dispatch.

Broad Explorer prompts include output/source/citation budget, artifact pointer,
and forbid raw dumps, copied source bodies, long logs, full matrices, recursive
subagents, and continuing after the packet. Codex research defaults to
`fork_context:false` unless all parent context is required.

When delegated work may change durable project memory, ask for `Memory Delta
Candidate` (`none | current | plan | research | decision | supersede | compact |
deferred`). Orchestrator decides writes.

Prefer Teamwork custom agents from `Codex Mapping`; otherwise use
`Codex Native Field Presets` unless `full-history-fork`. If `model` is omitted, write
`model: inherited` and why. Never imply a stronger model than the Native Fields request.

## Role Templates

```text
Explorer: platform native fields per platform-dispatch-mapping.md; one evidence question; read-only; Explorer Result Packet; stop.
Designer: compare options; read-only; Designer Decision Packet; stop.
Judge: review plan readiness; read-only; Judge Plan Review Packet; stop.
Worker: implement one owned slice; block on missing required values; Worker Completion Packet; stop.
Reviewer: review completed work; read-only; Reviewer Verdict Packet; stop.
```
