---
name: using-teamwork
description: Use when starting any coding-agent task including coding, debugging, implementation, planning, review, evidence gathering, accepted-plan execution, package updates, or goal-directed work.
---

# Using Teamwork

Teamwork is a Codex-first platform-native layer. Codex, Cursor, or Claude Code
does the work. It adds evidence, dispatch, review, memory, and goal convergence.
Labels: observed, inferred, claimed.

## References

Load focused references. `references/workflow-contract.md` owns judgment
and Platform Native Policy Map; `codex-deep-collaboration.md` Codex depth;
`dispatch-policy.md` dispatch economics; `platform-dispatch-mapping.md` native
fields; `workflow-orchestration.md` swarm work; `artifact-protocol.md` memory.

## Route Check

Evidence -> `skills/teamwork-research/SKILL.md`; init/slim -> `skills/teamwork-init/SKILL.md`; plan -> `skills/teamwork-plan/SKILL.md`; execute accepted plan -> `skills/teamwork-execute/SKILL.md`; review -> `skills/teamwork-review/SKILL.md`; update -> `skills/teamwork-update/SKILL.md`; goal loop -> `skills/teamwork-goal/SKILL.md`.

## Automatic Stage Selection

Do not wait for the user to name a Teamwork skill when intent is clear;
discovery reads frontmatter before routing.

- Planning: "plan", "design", "figure out", non-trivial "implement/fix/add/change"; unclear root/source/API/failure/evidence/risk routes research first.
- Init: "init", "initialize", "AGENTS", "CODEX", "CURSOR", "CLAUDE", "slim instructions", "workflow rules".
- Execution: "go ahead", "execute", "continue", "resume", "do it".
- Review: "review", "look over diff", or "check/validate completed work";
  simple checks stay native.
- Update: "version", "release", "changelog", "update Teamwork", "bump".
- Goal: "keep going", "until it passes", "iterate until done", or explicit
  budgeted convergence.

For autonomous convergence, route to `teamwork-goal` for chat-only `Goal Proposal`
before platform goal handoff unless an active goal surface exists.

## Orchestration Default

Stay native only for quick facts, tiny edits, credential work, tight
critical-path work, or higher subagent context cost. Do not
create artifacts, subagents, durable plans, or review ceremony for lightweight
work.

When a Teamwork route needs durable project memory, check
`docs/teamwork/index.json` first when present, then `active.current` or
`docs/teamwork/current.md` before deeper artifact reads.

Before staying native for non-trivial work, state scope, path, boundaries, and
success check; route unclear work to research.

When Teamwork is active, the main agent orchestrates. If subagents are
authorized, dispatch proactively for non-lightweight work: Explorer, Designer,
Judge, Worker, or Reviewer for independent evidence, design, implementation,
or review. Use fresh review when available; otherwise report unreviewed risk.

Plans may suggest routing; stage dispatch must not wait for named tracks or
plan phrases. On Codex, standing instructions can satisfy the explicit
subagent request; without authorization, keep local and record the exception.

Before treating subagents as unavailable for work that needs them, use the
Subagent Tool Discovery Gate. Skipped non-lightweight dispatch needs
`Dispatch Exception:`; if fresh review is unavailable, missing authorization,
or user-disabled, label non-lightweight acceptance as `unreviewed`.

## Route Output

For Teamwork routing, report `Route: teamwork-<stage>`, `Reason: ...`, and
`Mode: research | plan | execution | review | update | goal`. For native-flow
tasks, do not emit a route banner. Include `Memory Delta:` only when durable
project memory was checked or changed.
