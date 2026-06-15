# Subagent Prompt Contract

Delegated prompts. Native flow summarizes. For dispatch read
`dispatch-policy.md`; native fields, `platform-dispatch-mapping.md`; returned
shapes, `subagent-packets.md`.

## Context Strategies

- `condensed-evidence-only`: question, paths, commands, budget, expected packet.
- `artifact-backed`: artifact paths plus required sections.
- `owned-files-only`: owned paths, allowed edits, verification target.
- `fresh-context-review`: target, criteria, diff/artifacts, rejection rules, no parent reasoning.
- `full-history-fork`: side task needs parent context. Codex uses `fork_context:true`; Cursor uses `resume:"self"`; Claude passes condensed context.
- `explicit-non-inheriting-dispatch`: role/model/reasoning differs. Override Codex `agent_type`/model/reasoning, Cursor `subagent_type`/model, Claude `subagent_type`.

## Two-Layer Prompt Template

Use Role Card for native mechanics and Task Card for the mission.

```text
Role Card:
- Conceptual Role: Explorer, Designer, Judge, Worker, or Reviewer. Deep Judge/Reviewer are severity profiles.
- Native Fields: fields from `platform-dispatch-mapping.md` plus model class.
  Codex role dispatch uses `agent_type`, model/reasoning, and `fork_context:false`;
  full-history fork (`fork_context:true`, inherited model, no `agent_type/model/reasoning_effort`). Cursor uses `subagent_type`, `model` or inherited.
- Mode: read-only | workspace-write | review-only.
- Context Strategy: one value from `Context Strategies`.
- Closure Instruction: return packet once, then stop; orchestrator owns integration, final acceptance, and dispatch.

Task Card:
- Mission: one question, decision, slice, or review.
- Source: plan, research, report, diff, output, paths, artifacts.
- Inputs: files, commands, evidence, assumptions, required values, target.
- Owned Scope: files/components to inspect/edit.
- Allowed Actions: read-only | workspace-write | verification | review-only.
- Forbidden Actions: scope expansion, destructive operations, credentials, overlapping writes, unrelated cleanup, broad refactors, final acceptance, follow-on monitoring, chaining subagents, or continuing after packet.
- Verification Target: command/artifact/behavior/checklist.
- Escalation Triggers: missing context, missing required env/path/command/model/config values, unclear ownership, protected boundary, plan mismatch, destructive risk, auth failure, or uncertainty changing intent, acceptance, public behavior, architecture, or contracts. Subagents report questions; the orchestrator asks.
- Required Output Schema: packet from `subagent-packets.md`.
```

## Prompt Notes

Broad Explorer prompts include output/source/citation budget and artifact pointer; forbid raw dumps, long logs, recursive subagents, and continuing after packet. Codex research defaults to `fork_context:false` unless full parent context is required.

When delegated work may change durable project memory, ask for `Memory Delta Candidate` (`none|current|plan|research|decision|supersede|compact|deferred`). Orchestrator decides writes.

Prefer `Codex Mapping` custom agents; otherwise use `Codex Native Field Presets` unless `full-history-fork`. If `model` is omitted, write `model: inherited` and why. Never imply a stronger model than requested Native Fields.

Local/native lightweight flow may summarize naturally; material delegated tracks still return role-specific packet and closure evidence.

## Compact Examples

- Explorer snapshot: `Explorer`, read-only, `condensed-evidence-only`; one status snapshot; no write/kill/restart/monitoring; return Explorer Result Packet.
- Worker slice: `Worker`, workspace-write, `owned-files-only`; implement one accepted path slice; run proof; return Worker Completion Packet.
- Reviewer verdict: `Reviewer`, read-only, `fresh-context-review`; review diff against requirements/evidence; no fixes by default; return Reviewer Verdict Packet.

## Role Templates

```text
Explorer: platform native fields per platform-dispatch-mapping.md; one evidence question; read-only; Explorer Result Packet; stop.
Designer: compare options; read-only; Designer Decision Packet; stop.
Judge: readiness review; read-only; Judge Plan Review Packet; stop.
Worker: implement one owned slice; block on missing required values; Worker Completion Packet; stop.
Reviewer: completed-work review; read-only; Reviewer Verdict Packet; stop.
```
