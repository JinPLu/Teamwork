---
name: teamwork-execute
description: Use when an accepted plan, checklist, approved scope, or known root-cause fix should be implemented, continued, resumed, or verified with focused action.
---

# Teamwork Execute

Use after a plan, checklist, scope, or root-cause fix is accepted. Execution
carries out accepted scope; it does not expand scope. It reports implementation
and verification; review or goal mode owns non-lightweight acceptance.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence; `skills/using-teamwork/references/subagent-dispatch.md`
for Worker split; `skills/using-teamwork/references/role-playbook.md` for
Worker method; `skills/using-teamwork/references/subagent-contract.md` for
Worker prompts and packets; `skills/using-teamwork/references/artifact-protocol.md`
for durable memory; `skills/using-teamwork/references/debug-mode.md` for
bug/failure evidence and cleanup rules; `skills/using-teamwork/references/verification-patterns.md`
for proof strength and baseline/treatment evidence; `skills/using-teamwork/references/optional-skills.md`
before external tools; `skills/using-teamwork/references/grill-mode.md` when
grill mode is active.

## Preconditions

- An accepted plan, checklist, approved scope, or known root-cause fix whose
  decision-critical needs, acceptance, and constraints are resolved.
- Required files, commands, credentials, environments, paths, ports, models,
  hyperparameters, configs, and execution modes are explicit or discoverable.
- Explicit grill mode has either a confirmed Shared Understanding Packet or a
  user exit from grill mode.
- A durable plan path for goal-mode, cross-turn, high-risk, delegated, or
  artifact-backed work; read `docs/teamwork/index.json` then current-state
  pointers when durable memory is relevant.

If needed state is missing, inspect source/config first, ask once when a human
can supply it, and block only when it is unavailable, unsafe, declined, or would
invent a fallback, mask an invariant, switch targets, or add detours.

## Worker Boundary

Workers execute the accepted scope; they do not reopen behavior, architecture,
requirements, or scope. If evidence changes those, route back to research or
plan. Prefer TDD for behavior changes when practical; diagnose root cause before
fixing failures. Every slice needs an exit condition: passing proof, observed
artifact/behavior, structured validation, a bounded attempt limit, or a blocker.
Before editing code, trace the existing owner, control flow, tests/config, and
invariants enough to explain why the current path exists. Prefer reshaping the
existing path over adding a parallel mode, compatibility branch, wrapper, or
fallback. Keep implementation small and direct; do not grow branches to avoid
understanding the current code.
Fail fast rather than invent fallback behavior when accepted scope lacks a
required value or invariant. Do not add broad catches, nullable defaults, casts,
aliases, provider/target switches, or defensive branches that make missing state
look valid.

For reproducible but unclear failures where diagnosis is the task, route to
`teamwork-debug`. Use one bounded micro-debug pass locally when accepted scope
needs small confirming evidence before a targeted fix; if root cause is still
unclear, stop and route to Debug. Debug cleanup is narrow: remove
temporary instrumentation, logs, scaffolding, and obvious touched-diff slop
without broad refactor or unaccepted adjacent cleanup.

## Steps

1. Re-read the plan and relevant source, including the current owner/control
   flow and relevant tests or config before edits.
2. For non-lightweight work, fan out Workers for independent tracks with
   disjoint ownership or worktree isolation; keep tightly coupled work local.
   Before more than 3 Workers, state the ownership map, integration order, and
   verification plan. Start an Actual Dispatch Log when subagents run.
3. State the files you or Workers will touch.
4. Make only planned, minimal, producer-side changes; prefer simplifying the
   existing flow over accumulating branches or modes.
5. Integrate Worker packets, then record returned packets or blockers in the
   Actual Dispatch Log.
6. Run focused verification; cite command output, artifacts, diffs, or tests,
   and do not round blocked/build-only checks up to behavioral proof. Add
   broader checks only when planned or when shared/public behavior changes.
7. Stop if new evidence invalidates the plan.

## Handoff

Return implemented paths, plan source, verification evidence, cleanup evidence
when debug instrumentation was used, Actual Dispatch Log or continuity rationale,
deviations, and blockers. For
non-lightweight work, request a fresh-context Reviewer before claiming
completion; if subagents are unavailable, report the work as unreviewed with its
residual risk. Do not claim completion while any delegated track is open.
Include `Memory Delta:` only when durable project memory was checked or changed.
