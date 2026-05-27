---
name: using-teamwork
description: Use when starting any coding-agent task including coding, debugging, implementation, planning, review, evidence gathering, accepted-plan execution, package updates, or goal-directed work.
---

# Using Teamwork

Teamwork is a platform-native augmentation layer. Native Codex, Cursor, or
Claude Code capabilities do the work; Teamwork orchestration is the default for
coding-agent work that is not clearly lightweight. It adds evidence discipline,
stage routing, proactive dispatch, review, durable memory, and goal
convergence. Evidence labels: observed, inferred, claimed.

## References

Load focused references only. `references/workflow-contract.md` owns Evidence Interpretation Contract, Platform Native Policy Map, Context & Cost Discipline, and Subagent Collaboration Model; `dispatch-policy.md` owns Dispatch Economics.

## Route Check

| Signal | Route |
|---|---|
| Evidence | `skills/teamwork-research/SKILL.md` |
| Init/slim | `skills/teamwork-init/SKILL.md` |
| Plan edits | `skills/teamwork-plan/SKILL.md` |
| Execute accepted plan | `skills/teamwork-execute/SKILL.md` |
| Review | `skills/teamwork-review/SKILL.md` |
| Update | `skills/teamwork-update/SKILL.md` |
| Goal loop | `skills/teamwork-goal/SKILL.md` |

## Automatic Stage Selection

Do not wait for the user to name a Teamwork skill when intent is clear; discovery reads frontmatter before route filtering.

- Planning: "plan", "design", "figure out", non-trivial "implement/fix/add/change"; unclear root/source/API/failure/evidence/risk routes research first.
- Init: "init", "initialize", "AGENTS", "CODEX", "CURSOR", "CLAUDE", "slim instructions", "workflow rules".
- Execution: "go ahead", "execute", "continue", "resume", "do it".
- Review: "review", "check", "validate", "look over the diff".
- Update: "version", "release", "changelog", "update Teamwork", "bump".
- Goal: "keep going", "until it passes", "iterate until done", budget.

For autonomous convergence, route to `teamwork-goal` for chat-only `Goal Proposal`
before platform goal handoff unless an active goal surface exists.

## Orchestration Default

Native flow is only for quick factual answers, one-liners, and tiny obvious
edits. Do not create artifacts, subagents, durable plans, or review ceremony.

Before staying native for non-trivial work, state scope, path, boundaries, and
success check. If unclear, route to research.

When Teamwork is active, the main agent orchestrates. Apply Stage-Routed Proactive Dispatch before serial work: split independent tracks, use the
Subagent Tool Discovery Gate, then dispatch Explorer, Designer, Judge, Worker,
or Reviewer tracks unless an allowed `Dispatch Exception:` applies. Acceptance
needs a fresh Reviewer, not self-review.

Plans may suggest routing; stage dispatch must not wait for named tracks or
explicit phrases. The user does not need to ask to "fan out subagents".

Before treating subagents as unavailable, use the Subagent Tool Discovery Gate.
Skipped required dispatch needs `Dispatch Exception:`; non-lightweight
acceptance without a fresh Reviewer remains `unreviewed`.

## Route Output

For Teamwork routing, report:

```text
Route: teamwork-<stage>
Reason: <one sentence tied to intent>
Mode: <research | plan | execution | review | update | goal>
```

For native-flow tasks, do not emit a route banner.
