---
name: teamwork-plan
description: Use when the user asks for plan/design or a non-trivial research, engineering, or implementation change needs scope, requirements, protected boundaries, verification, dispatch, memory, or acceptance before action.
---

# Teamwork Plan

Use after research or user direction selects a path, and before non-trivial
project action when no accepted plan exists. Plans lock scope; tiny fixed-scope
work stays native or goes straight to execute.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence and judgment; `skills/using-teamwork/references/subagent-dispatch.md`
for when to fan out; `skills/using-teamwork/references/role-playbook.md` for
Designer/Judge method; `skills/using-teamwork/references/subagent-contract.md`
for delegated prompts and packets; `skills/using-teamwork/references/plan-output.md`
for durable plans; `skills/using-teamwork/references/artifact-protocol.md` for
artifact triggers; `skills/using-teamwork/references/debug-mode.md` for
bug/failure plans that need runtime diagnosis; `skills/using-teamwork/references/verification-patterns.md`
for falsifiable acceptance and proof strength; `skills/using-teamwork/references/grill-mode.md`
when explicit grill/question-first mode is active.

## Ask First

Resolve decision-critical gaps before planning. Ask when scope, acceptance,
constraints, risk, UX, public behavior, contracts, architecture, or
verification would change the plan. Route to `teamwork-research` when external
behavior, unfamiliar APIs, upstream bugs, or ambiguous architecture lack
evidence. Route to `teamwork-debug` when a reproducible failure needs runtime
evidence before fix scope is safe. Do not produce an execution plan while a
core requirement is open, or while active grill mode lacks a confirmed Shared
Understanding Packet. Do not dispatch Designer/Judge while that grill packet is
missing.

## Planning Tiers

Use the lightest form that stays correct:

- **Chat plan:** clear small-to-medium work — goal, scope, files, ordered
  steps, verification, and stop condition.
- **Durable plan:** goal-mode, cross-turn, high-risk, ambiguous, public
  behavior, long delegation, or explicit repo plans. Path
  `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`; see `plan-output.md`.
- **Goal plan:** autonomous or budgeted convergence. The native Codex goal or
  Cursor/Claude rolling report owns lifecycle; the plan owns the current
  approach, evidence, gates, budget, retry, and acceptance criteria.

## Workflow

1. Restate the goal/root cause and current state; label important evidence
   `observed`, `inferred`, or `claimed`.
2. Map requirements to evidence or planned verification.
   For bug, UI, performance, memory, migration, or parity claims, name any
   baseline/treatment evidence and expected verification strength.
3. Define in/out/protected scope and pick the smallest producer-side change.
   For code, name current owner/control flow, tests/config, and invariants.
4. Use Mermaid only for non-linear, delegated, or hard-to-audit flows. For three
   or more comparable items, use compact tables.
5. Make steps executable: each phase has owner, input, output, verification,
   result, and stop trigger.
   For bug work, state whether the route is `research -> plan -> execute`,
   `debug -> plan -> execute`, or `debug -> execute`.
6. Decide dispatch before finalizing steps. Split independent tracks to
   subagents with owned paths and packet shape, or keep local and state why.
7. For goal-mode retry plans, include Goal Invariants and Replay Preflight:
   prior attempts reviewed, do-not-repeat, strategy delta, and stop check.
8. Use Designer for ambiguous decisions and Judge before high-risk, durable,
   delegated, or goal-mode execution. If skipped, name the residual risk.
9. End with next actions that `teamwork-execute` or a Worker can run directly.

## Quality Bar

- Every planned artifact, file, or action traces to the goal.
- Human reviewability: expose important choices, comparable steps, and gates in
  compact tables or diagrams.
- Agent executability: no vague "handle/fix/update" steps without owned scope,
  inputs, outputs, verification, and stop rules.
- Required values/invariants — env, paths, commands, ports, models,
  hyperparameters, configs, credentials, execution modes, and fallback contracts
  — trace to user input, source/config, instructions, tests, accepted plan, or
  observed evidence; never invent them. Ask for human-only gaps; block when
  source values cannot be found.
- No broad refactor, abstraction, format churn, or downstream cleanup unless
  evidence requires it.
- Delegated plans name the prompt shape, ownership, and expected packet.
- Goal-mode durable plans include Search Keys, Abstract, Goal Invariants,
  budget, success signal, no-progress stop, retry/research trigger, and
  acceptance review.

## Output

Use bullets or a compact chat plan for lightweight work; use `plan-output.md`
for durable plans. Include `Memory Delta:` only when durable project memory was
checked or changed.
