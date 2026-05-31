# Codex Deep Collaboration

Use this reference when Teamwork runs on Codex and the work is not lightweight.
Codex is the reference runtime for Teamwork 1.0.

## Control Plane

- Native Codex goal state is the source of truth for autonomous lifecycle.
- Use `Goal Proposal` only when objective, scope, verification, or stop rules
  need human review before `create_goal`.
- Use `update_plan` for visible progress only; durable state lives in Teamwork
  artifacts and optional index/current files.

## Proactive Custom Agents

When user prompt, project rules, or global `AGENTS.md` provide standing
authorization, non-lightweight Teamwork stages dispatch proactively:

- Explorer for codebase orientation, artifact lookup, external calibration, or
  failure evidence that is not a quick literal read.
- Designer for ambiguous architecture or product-shape decisions.
- Judge for durable, high-risk, delegated, or goal-mode plans.
- Worker for independent implementation tracks with disjoint ownership.
- Reviewer for non-trivial plan execution, diffs, verification, or acceptance.

Keep the main agent as orchestrator. It owns scope, Worker boundaries,
integration, final verification, and Memory Delta. Skip dispatch only for quick
facts, tiny obvious edits, destructive or credential-sensitive work, tightly
coupled critical-path work, unavailable tools, missing authorization, explicit
user opt-out, or higher subagent context cost than value. Record
`Dispatch Exception:` when the skipped dispatch affects review or acceptance.

## Codex Operational Evidence

Use native Codex surfaces as evidence channels when relevant:

- Permission profiles: name the active profile or material filesystem/network
  boundary when it affects execution or dispatch.
- `codex doctor` and `/status`: prefer these before ad hoc environment
  debugging when setup, remote connection, or CLI state matters.
- Browser annotations, Appshots, Computer Use, and remote/Windows support:
  use when visual, desktop, remote, or OS-specific behavior is acceptance
  evidence.
- Plugins/connectors/MCP: use native tools first and record source limits when
  unavailable access affects a decision.

## Packaging

Skills remain the authoring surface. Plugins are the distribution surface. Keep
shared `SKILL.md` frontmatter portable; put Codex-specific depth in references,
custom agents, manifests, installer policy, and runtime docs.
