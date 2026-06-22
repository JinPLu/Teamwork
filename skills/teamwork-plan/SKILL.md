---
name: teamwork-plan
description: Use when the user asks for plan/design or a non-trivial implement/fix/add/change/refactor needs scope, requirements, protected boundaries, verification, dispatch, memory, or acceptance before edits.
---

# Teamwork Plan

Use after research or user direction selects a path, and before non-trivial
implementation when no accepted plan exists. Plans lock scope.

Mirror Cursor Plan Mode's useful contract: use existing user/source evidence
first, route to research only when evidence is missing or stale, ask only
requirement-changing questions, produce a reviewable Markdown plan before code,
then execute from the accepted plan. Teamwork adds evidence labels, dispatch,
goal surfaces, stop rules, and acceptance.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence and judgment; `skills/using-teamwork/references/subagent-dispatch.md`
for when to fan out; `skills/using-teamwork/references/role-playbook.md` for
Designer/Judge method; `skills/using-teamwork/references/subagent-contract.md`
for delegated prompts and packets; `skills/using-teamwork/references/plan-output.md`
for durable plans; `skills/using-teamwork/references/artifact-protocol.md` for
artifact triggers; `skills/using-teamwork/references/debug-mode.md` for
bug/failure plans that need runtime diagnosis; `skills/using-teamwork/references/verification-patterns.md`
for falsifiable acceptance and proof strength.

## Ask First

Resolve decision-critical gaps before planning. Ask when scope, acceptance,
constraints, risk, UX, public behavior, contracts, architecture, or
verification would change the plan. Route to `teamwork-research` when external
behavior, unfamiliar APIs, upstream bugs, or ambiguous architecture lack
evidence. Route to `teamwork-debug` when a reproducible failure needs runtime
evidence before fix scope is safe. Do not produce an execution plan while a
core requirement is open.

## Planning Tiers

Use the lightest form that stays correct:

- **Chat plan:** clear small-to-medium work — goal, scope, files, ordered
  steps, verification, and stop condition.
- **Durable plan:** goal-mode, cross-turn, high-risk, ambiguous, public/shared
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
4. For multi-stage or branching work, include a Mermaid flowchart. For three or
   more comparable items, use tables: status, phases, artifacts, gates,
   dispatch, and acceptance.
5. Make steps executable: each phase has owner, input, output, verification,
   expected result, and stop/replan trigger.
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

- Every planned file traces to the goal.
- Human reviewability: important choices, comparable steps, and gates are visible
  in compact tables or diagrams; prose explains only what tables cannot.
- Agent executability: no vague "handle/fix/update" steps without owned scope,
  inputs, outputs, verification, and stop rules.
- Required env vars, paths, commands, ports, models, hyperparameters, configs,
  credentials, and execution modes trace to user input, source/config,
  instructions, or observed evidence — never invented. Missing human
  requirements ask first; missing source values block only after they cannot be
  found.
- No broad refactor, abstraction, formatting churn, or downstream cleanup unless
  evidence requires it.
- Delegated plans name the prompt shape, ownership, and expected packet.
- Goal-mode durable plans include Search Keys, Abstract, Goal Invariants,
  budget, success signal, no-progress stop, retry/research trigger, and
  acceptance review.

## Output

Use bullets or a compact chat plan for lightweight work; use `plan-output.md`
for durable plans. Include `Memory Delta:` only when durable project memory was
checked or changed.
