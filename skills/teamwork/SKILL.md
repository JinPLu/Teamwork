---
name: teamwork
description: Use when routing multi-step, evidence-sensitive, high-risk, cross-agent, cross-turn, reviewed, or autonomous coding-agent work through the Teamwork stage skills.
---

# Teamwork

Teamwork is a workflow-preference layer over Claude Code, Codex, and Cursor. It
adds evidence discipline, scoped planning, bounded execution, fresh review, and
goal-mode convergence only when those gates improve the result.

Shared rules live in references and are loaded only when needed:

- `skills/teamwork/references/workflow-contract.md`: assumptions, Evidence Interpretation Contract, Context & Cost Discipline, Progress Anchors And Artifacts, and Subagent Collaboration Model.
- `skills/teamwork/references/artifact-protocol.md`: artifact triggers,
  research reuse, placeholder hygiene, and report roles.
- `skills/teamwork/references/subagent-routing.md`: Subagent Routing Policy,
  conceptual roles, model tier choices, Codex Dispatch Mapping, and
  full-history fork limits.
- `skills/teamwork/references/goal-iteration.md`: goal loop, failure gate, and
  rolling report format.

## Activation Tiers

| Tier | Use when | Planning | Review | Subagents |
|---|---|---|---|---|
| Native flow | Simple, local, low-risk work | None or native task list | Normal verification | Not needed |
| Lightweight Teamwork | Multi-step but bounded work | Concise chat/native checklist | Distinct self-review or focused review | Optional |
| Durable artifact | Cross-agent, cross-turn, high-risk, ambiguous, public/shared, or explicitly planned work | durable Markdown plan artifact | Plan/execution review against artifact | Documented if used or skipped |
| Goal mode | Explicit autonomous convergence | Mandatory durable artifact and runtime plan anchor | Mandatory passing review/checkpoint | As useful within budget |

native flow remains the default for simple Claude Code tasks.

Durable artifacts use:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

`update_plan` is transient UI-only checklist state. It is not a durable
execution spec, review target, or completion proof.

## Route By Intent

Use the narrowest subskill that adds value:

| Intent | Route | Skill file |
|---|---|---|
| Research options, compare approaches, root-cause investigate, or gather evidence | `teamwork-research` | `skills/teamwork-research/SKILL.md` |
| Convert a selected direction into an executable implementation plan | `teamwork-plan` | `skills/teamwork-plan/SKILL.md` |
| Execute an accepted plan with minimal edits and focused verification | `teamwork-execute` | `skills/teamwork-execute/SKILL.md` |
| Review a proposed plan | `teamwork-review` with `mode: plan` | `skills/teamwork-review/SKILL.md` |
| Review completed implementation, artifacts, tests, or diffs | `teamwork-review` with `mode: execution` | `skills/teamwork-review/SKILL.md` |
| Iterate autonomously until verified success, budget exhaustion, or blocker | `teamwork-goal` with `mode: goal` | `skills/teamwork-goal/SKILL.md` |

Do not create separate plan-review and execution-review subskills.

## Shared Contract

When a Teamwork stage is active, first read
`skills/teamwork/references/workflow-contract.md`. Important evidence is labeled
`observed`, `inferred`, or `claimed`; claimed labels never decide scope,
canonical files, or completion without direct corroboration.

Use subagents only when independent context, parallel evidence, isolated
execution, or fresh review improves correctness or speed. For non-lightweight
work, split the next decision into independent tracks first. Default to at most 3 parallel research/review subagents unless the user gives a larger budget.

When Teamwork is active, treat the user as granting standing authorization for
automatic subagent delegation on independent non-lightweight tracks. Do not ask
for extra "fan out" confirmation unless dispatch needs credentials,
destructive actions, unclear write ownership, or another approval-gated
capability.

## Codex Native Integration

- Use Codex native planning, subagents, reviews, goals, sandbox approvals, and
  skills; do not emulate Claude Stop hooks.
- Use native Codex goals only for explicit autonomous convergence or an active
  goal.
- Derive native dispatch fields from
  `skills/teamwork/references/subagent-routing.md` at dispatch time. Ordinary
  plans record conceptual role, scope, model tier, context strategy, order, and
  why.
- `fast`, `standard`, and `high reasoning` are capability tiers. `xhigh` is only
  for explicitly high-risk final gates where cost is justified.
- `codex review --uncommitted`, `--base`, or `--commit` can be review evidence,
  not an automatic pass.

## Route Output

For Teamwork routing, report:

```text
Route: teamwork-<stage>
Reason: <one sentence tied to user intent>
Mode: <research | plan | execution | goal, when applicable>
```

For native-flow tasks, do not emit a route banner.
