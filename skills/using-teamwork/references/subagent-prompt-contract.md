# Subagent Prompt Contract

Use when preparing a delegated prompt. For dispatch decisions read
`dispatch-policy.md`; for native fields read `platform-dispatch-mapping.md`;
for returned shapes read `subagent-packets.md`.

## Context Strategies

- `condensed-evidence-only`: question, paths, commands, and expected packet.
- `artifact-backed`: durable artifact paths plus required sections.
- `owned-files-only`: owned paths, allowed edits, and verification target.
- `fresh-context-review`: review target, criteria, diff/artifacts, rejection
  rules, and no parent reasoning.
- `full-history-fork`: side task needs nearly all parent context. Codex:
  `fork_context:true`. Cursor: `Task` with `resume:"self"`. Claude Code: pass
  condensed context inline.
- `explicit-non-inheriting-dispatch`: role, model tier, or reasoning differs.
  Codex: override `agent_type`, `model`, or `reasoning_effort`. Cursor:
  override `subagent_type` or `model`. Claude Code: choose a matching
  `subagent_type`.

## Required Fields

Every delegated prompt includes:

- Conceptual Role: Explorer, Designer, Judge, Worker, or Reviewer. Deep Judge
  and Deep Reviewer are Codex severity profiles for Judge/Reviewer, not new
  conceptual roles.
- Native Fields: platform dispatch fields from `platform-dispatch-mapping.md`.
  Codex: `agent_type`, `model` or `model: inherited`, `reasoning_effort`,
  `fork_context`; on Cursor `subagent_type`, `model` or `model: inherited`;
  Claude Code: `subagent_type`.
- Mission: one concrete question, decision, implementation slice, or review.
- Source: plan, research, report, diff, command output, or file paths.
- Inputs: exact files, commands, evidence, assumptions, and acceptance target.
- Owned Scope: files/components the subagent may inspect or edit.
- Allowed Actions: read-only, workspace-writing, verification, or review-only.
- Forbidden Actions: scope expansion, destructive operations, credentials,
  overlapping writes, unrelated cleanup, broad refactors, final acceptance,
  follow-on monitoring, chaining subagents, or continuing after the packet.
- Context Strategy: one value from `Context Strategies`.
- Verification/Acceptance Target: command, artifact, behavior, or checklist.
- Escalation Triggers: missing context, unclear ownership, protected boundary,
  plan mismatch, destructive risk, auth failure, or uncertainty changing public
  behavior, architecture, or contracts.
- Required Output Schema: matching packet from `subagent-packets.md`.
- Closure Instruction: return the required packet once, then stop; the
  orchestrator owns integration, final acceptance, and any further dispatch.

When delegated work may change durable project memory, ask for `Memory Delta
Candidate` (`none | current | plan | research | decision | supersede | compact |
deferred`). The orchestrator decides writes.

For Codex, prefer Teamwork custom agents from `Codex Mapping`; otherwise fill
native fields from `Codex Native Field Presets` unless using
`full-history-fork`. If `model` is omitted, write `model: inherited` and why.
If pinned, write model class and reason. Never imply a stronger model than the
Native Fields request.

## Role Templates

```text
Explorer: platform native fields per platform-dispatch-mapping.md; answer one evidence question; read-only; output Explorer Result Packet once, then stop.
Designer: compare options and choose a direction; read-only; output Designer Decision Packet once, then stop.
Judge: review plan readiness before execution; read-only; output Judge Plan Review Packet once, then stop. Use Deep Judge native fields only for high-risk severity.
Worker: implement one owned slice; write owned scope only; output Worker Completion Packet once, then stop.
Reviewer: review completed work after execution; read-only; output Reviewer Verdict Packet once, then stop. Use Deep Reviewer native fields only for high-risk severity.
```
