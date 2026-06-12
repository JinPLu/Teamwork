---
name: teamwork-plan
description: Use when explicit planning/design or non-trivial implement/fix/add/change/refactor needs scope, verification, dispatch, memory, or acceptance before edits; skip tiny router-fast-path edits.
---

# Teamwork Plan

Use after research, diagnosis, or user direction selects a path. Also use
before non-trivial implementation when no accepted plan exists. Plans lock scope.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence and boundaries.
- `skills/using-teamwork/references/dispatch-policy.md` for Dispatch Guidance.
- `skills/using-teamwork/references/role-workflows.md` for Designer/Judge method.
- `skills/using-teamwork/references/designer-judge-workflow.md` for option matrix and Judge gates.
- `skills/using-teamwork/references/optional-skills.md` for external skills.
- `skills/using-teamwork/references/subagent-prompt-contract.md` for delegated prompts.
- `skills/using-teamwork/references/plan-output.md` for durable handoffs.
- `skills/using-teamwork/references/artifact-protocol.md` for durable triggers.
- `skills/using-teamwork/references/goal-iteration.md` for failed goal-plan revision.

## Inputs

Goal, evidence, scope, protected boundaries, verification target, budget, and
stop rules. If external behavior, unfamiliar APIs, upstream bugs, or ambiguous
architecture lack evidence, route to `teamwork-research`.

## Planning Tiers

Use the lightest planning form that preserves correctness after the
Clarification Gate has run.

- Plan-as-you-go: for small-to-medium clear work with explicit intent, scope,
  and acceptance; state scope, files, verification, and stop condition, then
  continue. Ask first if a missing answer could change behavior, UX, contracts,
  architecture, verification, or protected boundaries.
- Lightweight plan: bounded low-risk work; include goal, scope, Dispatch
  Guidance only when dispatch matters, steps, verification, and stop condition.
  Use `Dispatch Guidance: none` only when a non-lightweight plan serializes
  meaningful independent tracks; otherwise omit dispatch fields for native fast
  path work.
- Durable plan: required for goal-mode, cross-turn, high-risk, ambiguous,
  public/shared behavior, long delegation, complex Worker fan-out, or explicit
  repository-plan requests.

Default durable path: `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`.

## Workflow

1. Restate goal/root cause and label evidence `observed`, `inferred`, or
   `claimed`.
2. Resolve decision-critical human requirement gaps before planning. Record
   `Clarification Gate: pass | ask | assumptions-stated | blocked-for-clarification`;
   ask when scope, acceptance, constraints, risk, UX, public behavior,
   contracts, architecture, or verification would change.
3. Build Requirements Mapping from each requirement to evidence or
   verification.
4. Define in/out/protected scope and choose the smallest producer-side change.
5. Run the Parallelization Gate before implementation steps when work is
   non-lightweight or dispatch would affect risk, cost, or review. Split
   independent valuable tracks, apply the Subagent Tool Discovery Gate when
   subagents are authorized, or emit `Dispatch Exception:` with the allowed
   reason.
6. Use Designer workflow for ambiguous choices unless observed evidence already
   fixes the decision. Use Judge workflow before delivering high-risk, durable,
   delegated, or goal-mode plans; if unavailable after discovery or explicitly
   opted out, label the plan `unreviewed`. Record Designer/Judge packet
   summaries in chat plans or the durable plan when used.
7. Write `Dispatch Guidance:` or durable `Subagent Routing`; guidance helps
   execution but is not the only dispatch authorization.
8. If external skills are in scope, apply `optional-skills.md`; plans may
   document install gates, but must not auto-install optional skills.
9. Add Subagent Prompt Packets only for delegated roles.
10. Write ordered steps, verification, Expected Results, risks, stop rules, and
   handoffs.

## Quality Gates

- Every planned file traces to the goal.
- Clarification Gate is `pass` or narrow `assumptions-stated`; `ask` or
  `blocked-for-clarification` means no execution plan until the user answers.
- Required env vars, paths, commands, ports, model names, hyperparameters,
  configs, credentials, and execution modes trace to user input, source/config,
  project instructions, or observed evidence; missing values are blockers.
- No broad refactor, abstraction, formatting churn, or downstream cleanup
  unless evidence requires it.
- `Dispatch Guidance: none` requires a continuity rationale only when dispatch
  would otherwise be material.
- Durable/high-risk/ambiguous plans require Judge verdict or an explicit
  `Dispatch Exception:` and `unreviewed` label.
- Delegated plans name prompt contract, context strategy, ownership, and
  Required Output Schema.
- Goal-mode durable plans include Search Keys and Abstract.
- Platform native dispatch fields are derived at dispatch time from the active
  stage decision and runtime platform, not copied blindly from plan prose.

## Output

Use bullets or a compact chat plan for lightweight work. For durable plans, use
`skills/using-teamwork/references/plan-output.md`.
Include `Memory Delta:` only when durable project memory was checked or
changed.
