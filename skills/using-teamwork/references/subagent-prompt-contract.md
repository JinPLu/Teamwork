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
  and explicit routing overrides are not needed.
- `explicit-non-inheriting-dispatch`: when role, model tier, or reasoning
  effort must differ from the parent.

## Required Fields

Every delegated prompt includes:

- Conceptual Role: Explorer, Designer, Judge, Worker, or Reviewer.
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

## Role Templates

```text
Explorer: answer <evidence question>; read-only; output Explorer Result Packet.
Designer: compare <decision options>; read-only; output Designer Decision Packet.
Judge: review <plan> readiness; read-only; output Judge Plan Review Packet.
Worker: implement <owned slice>; write only owned scope; output Worker Completion Packet.
Reviewer: review <target> against criteria; read-only; output Reviewer Verdict Packet.
```
