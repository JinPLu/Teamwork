---
name: teamwork-review
description: Use when reviewing a plan, diff, completed implementation, or before claiming non-trivial Teamwork work is complete.
---

# Teamwork Review

Use for required non-lightweight acceptance and for distinct reviewer passes
when review adds value. Review reads direct evidence, preserves dissent, and
does not rely only on planner/executor/tool summaries.

Read only as needed:

- `skills/using-teamwork/references/workflow-contract.md` for evidence and context rules.
- `skills/using-teamwork/references/review-checks.md` for plan/execution gates.
- `skills/using-teamwork/references/role-workflows.md` for Reviewer method and
  review-reception discipline.
- `skills/using-teamwork/references/reviewer-workflow.md` for fresh review,
  severity crosswalk, PR/CI provenance, feedback disposition, and re-review
  closure.
- `skills/using-teamwork/references/optional-skills.md` when reviewing
  proposed or used external skills.
- `skills/using-teamwork/references/dispatch-policy.md` for Reviewer dispatch and routing checks.
- `skills/using-teamwork/references/subagent-prompt-contract.md` before Reviewer prompts.
- `skills/using-teamwork/references/subagent-packets.md` for Reviewer Verdict Packet.
- `skills/using-teamwork/references/goal-iteration.md` for goal failure routing.
- `skills/using-teamwork/references/artifact-protocol.md` when review needs
  durable memory or current-state lookup.

## Shared Rules

- Choose `mode: plan` or `mode: execution`.
- Default to fresh-context Reviewer subagents for non-lightweight plan/execution
  acceptance when subagents are authorized.
  Same-context self-review is not acceptance.
- Local review is allowed only for lightweight work, subagent tools unavailable
  after the Subagent Tool Discovery Gate, missing authorization, or explicit
  user opt-out; label any non-lightweight verdict as unreviewed.
- Inspect source, diff, logs, tests, command output, artifacts, research, plan,
  and user constraints.
- Label important evidence `observed`, `inferred`, or `claimed`.
- Treat executor summaries, `codex review` (Codex), `code-reviewer` subagent
  output (Cursor or Claude Code), git diff, CI summaries, test runner output,
  and tool output as evidence inputs, not final verdicts.
- Do not fix issues during review unless explicitly asked.
- Use `blocker`, `major`, `minor` consistently: unsafe/impossible acceptance,
  required-before-proceed, or follow-up/note.
- When reviewing optional skills, reject duplicate installs, unclear
  source/license, broad write risk, missing credentials, or missing smoke test.
- Reviewer dispatch follows the same closure rule: return one verdict packet,
  integrate it, and close or block the track before acceptance.
- When durable memory is relevant, read `docs/teamwork/index.json` then
  `active.current`/`docs/teamwork/current.md`, or header-search relevant
  artifacts before verdict; record Artifact Retrieval disposition.

## Plan Review

Use `review-checks.md` for scope, assumptions, requirements mapping, evidence,
verification, risks, handoffs, routing, missing Parallelization Gate, prompt
contract, Required Output Schema, and protected-boundary changes.

## Execution Review

Use `review-checks.md` for diff scope, plan conformance, verification,
Routing conformance, Actual Dispatch Log, Worker Completion Packet, Reviewer
Verdict Packet, dispatch economics, workspace hygiene, and next failure route.
Confirm Stage-Routed Proactive Dispatch was evaluated even when the plan did not
name every track. Reject open delegated tracks without blocker rationale.
For re-review after `revise`, require prior verdict, required fixes reviewed,
fix evidence, remaining issues, and re-review verdict.

## Verdict Format

```text
Mode: plan | execution
Evidence Read:
- <observed|inferred|claimed> <path/command/artifact>: <finding>
Artifact Retrieval: none | index | reuse | update | new - <evidence/boundary>
Requirements / Evidence Map:
- <requirement or plan step> -> <evidence> -> <pass|fail|partial|not reviewed>
Findings:
- [blocker|major|minor] <issue> - <evidence> - <required action>
Dissent / Uncertainty: <none or concern>
Verdict: accept | revise | blocked
Rationale: <brief evidence-based reason>
```

Include `Memory Delta:` only when durable project memory was checked or
changed. When current-state files changed, review should verify the change is
material and evidence-backed.
