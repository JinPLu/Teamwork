# Subagent Prompt Contract

Use when preparing a delegated prompt. For dispatch decisions read
`dispatch-policy.md`; for returned shapes read `subagent-packets.md`.

## Context Strategies

- `condensed-evidence-only`: question, paths, commands, and expected packet.
- `artifact-backed`: durable artifact paths plus required sections.
- `owned-files-only`: owned paths, allowed edits, and verification target.
- `fresh-context-review`: review target, criteria, diff/artifacts, rejection
  rules, and no parent reasoning.
- `full-history-fork`: only when the side task needs nearly all parent context
  and explicit routing overrides are not needed. Codex: `fork_context:true`.
  Cursor: `Task` with `resume:"self"`. Claude Code: not directly supported;
  pass condensed context inline instead.
- `explicit-non-inheriting-dispatch`: when role, model tier, or reasoning must
  differ from the parent. Codex: override `agent_type`, `model`, or
  `reasoning_effort`. Cursor: override `subagent_type` or `model`. Claude
  Code: choose a `subagent_type` whose agent definition has the desired model
  and tool scope.

## Required Fields

Every delegated prompt includes:

- Conceptual Role: Explorer, Designer, Judge, Worker, or Reviewer.
- Native Fields: platform dispatch fields from `dispatch-policy.md` — on Codex
  `agent_type`, `model` or `model: inherited`, `reasoning_effort`, and
  `fork_context`; on Cursor `subagent_type`, `model` or `model: inherited`;
  on Claude Code `subagent_type` (model lives on the agent definition).
- Mission: one concrete question, decision, implementation slice, or review.
- Source: plan, research, report, diff, command output, or file paths.
- Inputs: exact files, commands, evidence, assumptions, and acceptance target.
- Owned Scope: files/components the subagent may inspect or edit.
- Allowed Actions: read-only, workspace-writing, verification, or review-only.
- Forbidden Actions: scope expansion, destructive operations, credentials,
  overlapping writes, unrelated cleanup, broad refactors, final acceptance.
- Context Strategy: one value from `Context Strategies`.
- Verification/Acceptance Target: command, artifact, behavior, or checklist.
- Escalation Triggers: missing context, unclear ownership, protected-boundary
  conflict, plan mismatch, destructive risk, auth failure, or uncertainty that
  changes public behavior, architecture, or contracts.
- Required Output Schema: matching packet from `subagent-packets.md`.

For Codex, prefer installed Teamwork custom agents from `Codex Mapping`; when
falling back to built-ins, fill native fields from `Codex Native Field Presets`
unless using `full-history-fork`. If `model` is omitted, write
`model: inherited` and why inheritance is safer than an explicit Role Profile
model. If `model` is pinned, write the model class and reason for the override.
Never imply a stronger model than the Native Fields request.

## Role Templates

```text
Explorer: native fields <platform native fields per dispatch-policy.md>; answer <evidence question>; read-only; output Explorer Result Packet.
Designer: native fields <platform native fields per dispatch-policy.md>; compare <decision options>; read-only; output Designer Decision Packet.
Judge: native fields <platform native fields per dispatch-policy.md>; review <plan> readiness; read-only; output Judge Plan Review Packet.
Worker: native fields <platform native fields per dispatch-policy.md>; implement <owned slice>; write only owned scope; output Worker Completion Packet.
Reviewer: native fields <platform native fields per dispatch-policy.md>; review <target> against criteria; read-only; output Reviewer Verdict Packet.
```
