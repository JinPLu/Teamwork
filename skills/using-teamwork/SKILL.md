---
name: using-teamwork
description: Use when starting any coding-agent task including coding, debugging, implementation, planning, review, evidence gathering, accepted-plan execution, package updates, or goal-directed work.
---

# Using Teamwork

Teamwork is a Codex-native augmentation layer. Codex native capabilities do the
work; Teamwork adds routing, evidence discipline, review, durable memory,
subagent policy, version hygiene, and goal convergence only when useful.

This entrypoint is broad because discovery reads frontmatter before this body.
After loading, keep simple work native; route only when Teamwork adds value.

## References

Load only what applies:

- `skills/using-teamwork/references/workflow-contract.md`: Evidence Interpretation Contract (`observed`, `inferred`, `claimed`), Context & Cost Discipline, Codex Native Policy Map, Subagent Collaboration Model, Dispatch Economics, and Proposal/Plan Routed authorization.
- `skills/using-teamwork/references/artifact-protocol.md`: durable memory.
- `skills/using-teamwork/references/subagent-routing.md`: role-specific dispatch economics.
- `skills/using-teamwork/references/goal-iteration.md`: goal loop and
  `Goal Proposal`.
- `skills/using-teamwork/references/plan-output.md`: plan output templates.
- `skills/using-teamwork/references/review-checks.md`: review checklists.

## Route Check

| Signal | Route | Skill file |
|---|---|---|
| Need evidence before choosing | `teamwork-research` | `skills/teamwork-research/SKILL.md` |
| Need a plan before non-trivial edits | `teamwork-plan` | `skills/teamwork-plan/SKILL.md` |
| Accepted plan/checklist needs edits | `teamwork-execute` | `skills/teamwork-execute/SKILL.md` |
| Plan, diff, or result needs scrutiny | `teamwork-review` | `skills/teamwork-review/SKILL.md` |
| Version, release, installer, or skill topology update | `teamwork-update` | `skills/teamwork-update/SKILL.md` |
| Iterate until verified success, budget, or blocker | `teamwork-goal` | `skills/teamwork-goal/SKILL.md` |

If none applies, continue without a route banner.

## Automatic Stage Selection

Do not wait for the user to name a Teamwork skill when intent is clear.

- Planning: "plan", "design", "figure out", non-trivial "implement/fix/add/change".
- Execution: "go ahead", "execute", "continue", "resume", "do it".
- Review: "review", "check", "validate", "look over the diff".
- Update: "version", "release", "changelog", "update Teamwork", "bump".
- Goal: "keep going", "until it passes", "iterate until done", budget.

For autonomous convergence, route to `teamwork-goal` for a chat-only
`Goal Proposal` before changing native Codex goal state unless an active goal
already exists.

## Native Default

Native flow is correct for quick factual answers, one-liners, and small
isolated edits with obvious verification. Do not create artifacts, subagents,
durable plans, or review passes for ceremony.

Before staying native for non-trivial work, confirm the behavior/scope
assumption, smallest path, boundaries, and success check. If unclear, route to
`teamwork-research` or `teamwork-plan`.

## Route Output

For Teamwork routing, report:

```text
Route: teamwork-<stage>
Reason: <one sentence tied to intent>
Mode: <research | plan | execution | review | update | goal>
```

For native-flow tasks, do not emit a route banner.
