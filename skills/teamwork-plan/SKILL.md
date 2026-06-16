---
name: teamwork-plan
description: Use when explicit planning/design or non-trivial implement/fix/add/change/refactor needs scope, verification, dispatch, memory, or acceptance.
---

# Teamwork Plan

Use after research or user direction selects a path, and before non-trivial
implementation when no accepted plan exists. Plans lock scope.

Read as needed: `skills/using-teamwork/references/workflow-contract.md` for
evidence and judgment; `skills/using-teamwork/references/subagent-dispatch.md`
for when to fan out; `skills/using-teamwork/references/role-playbook.md` for
Designer/Judge method; `skills/using-teamwork/references/subagent-contract.md`
for delegated prompts and packets; `skills/using-teamwork/references/plan-output.md`
for durable plans; `skills/using-teamwork/references/artifact-protocol.md` for
artifact triggers; `skills/using-teamwork/references/optional-skills.md` for
external tools.

## Ask First

Resolve decision-critical gaps before planning. Ask when scope, acceptance,
constraints, risk, UX, public behavior, contracts, architecture, or
verification would change the plan. Route to `teamwork-research` when external
behavior, unfamiliar APIs, upstream bugs, or ambiguous architecture lack
evidence. Do not produce an execution plan while a core requirement is open.

## Planning Tiers

Use the lightest form that stays correct:

- **Plan-as-you-go:** clear small-to-medium work — state scope, files,
  verification, and stop condition, then proceed.
- **Lightweight plan:** bounded low-risk work — goal, scope, steps,
  verification, stop condition.
- **Durable plan:** goal-mode, cross-turn, high-risk, ambiguous, public/shared
  behavior, long delegation, or explicit repo plans. Path
  `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`; see `plan-output.md`.

## Workflow

1. Restate the goal or root cause; label evidence `observed`, `inferred`, or
   `claimed`, and match confidence to evidence.
2. Map each requirement to evidence or a verification step.
3. Define in/out/protected scope and choose the smallest producer-side change.
4. When work is non-lightweight, decide the dispatch split before writing steps:
   split independent tracks to subagents with clear ownership, or keep local and
   note why.
5. Use Designer method for ambiguous choices; use Judge review before delivering
   high-risk, durable, delegated, or goal-mode plans. If review is skipped after
   discovery, name the residual risk.
6. Write ordered steps, verification, expected results, risks, stop rules, and
   handoffs.

## Quality Bar

- Every planned file traces to the goal.
- Required env vars, paths, commands, ports, models, hyperparameters, configs,
  credentials, and execution modes trace to user input, source/config,
  instructions, or observed evidence — never invented. Missing human
  requirements ask first; missing source values block only after they cannot be
  found.
- No broad refactor, abstraction, formatting churn, or downstream cleanup unless
  evidence requires it.
- Delegated plans name the prompt shape, ownership, and expected packet.
- Goal-mode durable plans include Search Keys and an Abstract.

## Output

Bullets or a compact chat plan for lightweight work; `plan-output.md` for
durable plans. Include `Memory Delta:` only when durable project memory was
checked or changed.
