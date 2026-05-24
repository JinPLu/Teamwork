---
name: teamwork
description: Use when routing multi-step, evidence-sensitive, high-risk, cross-agent, cross-turn, reviewed, or autonomous coding-agent work through the Teamwork stage skills.
---

# Teamwork

Teamwork is a Codex-native augmentation layer. Codex native capabilities are the
execution substrate; Teamwork adds evidence discipline, goal design, scoped
planning, bounded execution, fresh review, artifact memory, subagent routing,
and goal-mode convergence policy only when those gates improve the result.

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
| Native flow | Simple, local, low-risk work | None or native `update_plan` | Normal verification | Not needed |
| Lightweight Teamwork | Multi-step but bounded work | Concise chat/native checklist | Distinct self-review or focused review | Optional |
| Durable artifact | Cross-agent, cross-turn, high-risk, ambiguous, public/shared, or explicitly planned work | durable Markdown plan artifact | Plan/execution review against artifact | Documented if used or skipped |
| Goal mode | Explicit autonomous convergence | Native goal plus durable memory when triggers apply | Passing verification and review | Proposal/Plan Routed |

native flow remains the default for simple Codex tasks.

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

If a goal request is not already well formed, `teamwork-goal` first returns a
chat-only `Goal Proposal` for human review. Native Codex goal state is created
or revised only after the human accepts or edits that proposal, unless an
active goal already exists.

## Shared Contract

When a Teamwork stage is active, first read
`skills/teamwork/references/workflow-contract.md`. Important evidence is labeled
`observed`, `inferred`, or `claimed`; claimed labels never decide scope,
canonical files, or completion without direct corroboration.

Use subagents only when independent context, parallel evidence, isolated
execution, or fresh review improves correctness or speed. For non-lightweight
work, split the next decision into independent tracks first. Default to at most
3 parallel research/review subagents unless the user gives a larger budget.

Subagent authorization is Proposal/Plan Routed: an accepted Goal Proposal or
durable plan with Subagent Routing authorizes those independent tracks. Ask
again when dispatch needs credentials, destructive actions, unclear write
ownership, or another approval-gated capability.

## Codex Native Policy Map

- Native goal: Codex goal state is the source of truth for autonomous target and
  lifecycle. Teamwork designs objective, done evidence, scope, retry policy,
  artifact needs, and routing before `create_goal`.
- `update_plan`: transient UI progress only, not a durable execution spec,
  review target, or completion proof.
- Subagents: derive native dispatch fields from
  `skills/teamwork/references/subagent-routing.md` at dispatch time. Ordinary
  plans record conceptual role, scope, model tier, context strategy, order, and
  why.
- Review: `codex review --uncommitted`, `--base`, or `--commit` can be review
  evidence, not an automatic pass.
- Sandbox and permissions: use Codex native approval flows; Teamwork records
  risk, boundary, and ownership decisions.
- Automations and heartbeats: use native Codex automation/thread heartbeat for
  recurring checks or later continuation, not Teamwork artifacts.
- MCP and plugins: prefer native Codex tools and connectors; record source
  limits when they affect evidence or acceptance.
- `fast`, `standard`, and `high reasoning` are capability tiers. `xhigh` is only
  for explicitly high-risk final gates where cost is justified.

## Route Output

For Teamwork routing, report:

```text
Route: teamwork-<stage>
Reason: <one sentence tied to user intent>
Mode: <research | plan | execution | goal, when applicable>
```

For native-flow tasks, do not emit a route banner.
