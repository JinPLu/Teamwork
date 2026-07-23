---
name: teamwork-plan
description: Use when the user asks for an implementation plan, task breakdown, checklist, roadmap, or handoff for a direction and contract already selected, or a host requires that execution plan; do not use to brainstorm or settle product/architecture choices, research external facts, diagnose failures, review a candidate, or execute changes.
---

# Teamwork Plan

Translate an already selected direction into work that can be executed without
redesign. Every Plan invocation defaults to a durable Plan in an initialized
writable project unless the user says `no files`, `off-record`, `read-only`, `no
writes`, or equivalent. Planner produces an execution-ready Plan packet only;
Writer saves or rewrites it. Do not redesign or implement.

## Readiness

Confirm outcome, chosen direction, scope, protected boundaries, and acceptance
signals are settled. Inspect local owners, flow, interfaces, tests,
configuration, and commands needed for concrete steps. Do not ask for
discoverable facts or turn safe implementation details into user decisions.

When a prior Teamwork Design is claimed, require the controlled durable Design
path and revision returned by its transaction. Run
`discussion-transaction.py design-inspect --project-root <project>` and confirm
the active path/revision match the claim and `active.acceptance == accepted`.
Pending or blocked Design records are durable but never Plan-ready. Older v1/v2
controlled Design records count as accepted only when `design-inspect` reports
accepted. A conversational Design recommendation, adversarial audit result,
Grill record, hand-written file, or failed transaction is not Plan-ready and
must not be promoted by Planner.

If an open choice would change behavior, architecture, public contracts, data,
permissions, migration, or scope, stop and state the exact decision needed. Do
not compare options or hide it as an assumption. Missing implementation details
may remain prerequisites that block only dependent steps.

## Plan Shape

Lead with result and scope. Produce owned, ordered actions with dependencies and
direct proof. Each work unit identifies:

- the owner or target surface;
- the concrete change and preserved invariant;
- dependencies and values that must come from source rather than invention;
- the nearest direct success check;
- any public-boundary, migration, rollout, or rollback proof that is actually
  required.

Keep steps outcome-sized: meaningful and verifiable. Name parallel tracks only
when truly independent and give each non-overlapping ownership. Put real
execution before optional cleanup. Use tests to prove the result, not replace an
available real run.

End with explicit stop or replan conditions: new evidence changes the selected
direction or criteria; required authority or source values are absent; a
protected boundary cannot be verified; or the planned owner is not the real
owner. Do not add a confirmation turn when no decision remains.

Independent Plan Review runs only when the user requests it or a named material
risk gate requires it. When invoked, the reviewer freezes the selected direction,
scope, criteria, protected boundaries, candidate Plan, and direct local evidence;
it returns stable `PR-*` findings and `ACCEPT`, `REVISE`, or `BLOCKED`. Combine
its findings into one repair batch. The same reviewer may perform at most one
bounded delta recheck for that Plan; materially expanded scope requires a fresh
review decision. A reviewed Plan cannot pass with placeholders, ellipses, guessed
values, unresolved alternatives, `or its replacement`, vague “handle edge cases”
work, or redesign disguised as a step. An unreviewed Plan must not be described
as independently accepted.

Return a bounded Plan packet: purpose/audience, facts/sources, frozen
decision/status, style/structure, artifact kind/consumer, preserve/forbid,
direction, scope, steps, dependencies, proof, and stops. Writer uses
`artifact-inspect -> artifact-schema <create|update|supersede> -> artifact-apply`;
the transaction derives the destination and registers the ordinary index. Writer
may polish expression but not research, invent, or alter facts, authority, status,
proof, decisions, or acceptance. Missing project memory, Writer, brief,
authority, consumer, or transaction blocks only persistence: return the Plan and
report it unsaved/blocked. No Planner, Root, or Worker fallback writes it. Plan
approval does not authorize implementation, release, external effects, or destructive action.
