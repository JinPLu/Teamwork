---
name: using-teamwork
description: Use when starting any coding-agent task including coding, debugging, implementation, planning, review, evidence gathering, accepted-plan execution, package updates, or goal-directed work.
---

# Using Teamwork

Teamwork is a Codex-native augmentation layer. Codex native capabilities do the
work; Teamwork adds evidence discipline, stage routing, proactive dispatch,
review, durable memory, version hygiene, and goal convergence when useful.

Keep simple work native. Route only when Teamwork changes the outcome.

## References

- `references/workflow-contract.md`: Evidence Interpretation Contract
  (`observed`, `inferred`, `claimed`), Codex Native Policy Map,
  Context & Cost Discipline, Subagent Collaboration Model.
- `references/dispatch-policy.md`: Dispatch Economics, roles,
  Stage-Routed Proactive Dispatch, Codex mapping.
- `references/subagent-prompt-contract.md`: Context Strategies and prompt
  fields.
- `references/subagent-packets.md`: packet schemas and Actual Dispatch Log.
- `references/artifact-protocol.md`: durable memory.
- `references/goal-iteration.md`: `Goal Proposal` and retry loop.
- `references/plan-output.md`: plan templates.
- `references/review-checks.md`: review gates.
- `references/project-init.md`: instruction layering and MCP/search policy.

## Route Check

| Signal | Route |
|---|---|
| Need evidence before choosing | `skills/teamwork-research/SKILL.md` |
| Initialize/slim project instructions or migrate workflow rules | `skills/teamwork-init/SKILL.md` |
| Need a plan before non-trivial edits | `skills/teamwork-plan/SKILL.md` |
| Accepted plan/checklist needs edits | `skills/teamwork-execute/SKILL.md` |
| Plan, diff, or result needs scrutiny | `skills/teamwork-review/SKILL.md` |
| Version, release, installer, or topology update | `skills/teamwork-update/SKILL.md` |
| Iterate until verified success, budget, or blocker | `skills/teamwork-goal/SKILL.md` |

## Automatic Stage Selection

Do not wait for the user to name a Teamwork skill when intent is clear; discovery reads frontmatter before route filtering.

- Planning: "plan", "design", "figure out", non-trivial "implement/fix/add/change" after evidence; unclear root/source/API/failure/evidence/risk routes research first.
- Init: "init", "initialize", "AGENTS", "CODEX", "CLAUDE", "slim instructions", "workflow rules".
- Execution: "go ahead", "execute", "continue", "resume", "do it".
- Review: "review", "check", "validate", "look over the diff".
- Update: "version", "release", "changelog", "update Teamwork", "bump".
- Goal: "keep going", "until it passes", "iterate until done", budget.

For autonomous convergence, route to `teamwork-goal` for chat-only `Goal
Proposal` before native goal state unless an active goal exists.

## Native Default

Native flow is correct for quick factual answers, one-liners, and small edits
with obvious verification. Do not create artifacts, subagents, durable plans,
or review passes for ceremony.

Before staying native for non-trivial work, state scope, path, boundaries, and
success check. If unclear, route to research.

When Teamwork is active, the main agent orchestrates. For non-lightweight work,
apply Stage-Routed Proactive Dispatch before serial work; acceptance needs a
fresh Reviewer, not self-review. Plans may suggest routing; stage dispatch need not
wait for named tracks.

## Route Output

For Teamwork routing, report:

```text
Route: teamwork-<stage>
Reason: <one sentence tied to intent>
Mode: <research | plan | execution | review | update | goal>
```

For native-flow tasks, do not emit a route banner.
