# Review Checks

Use this reference for `teamwork-review` when a plan or implementation needs
evidence-based scrutiny.

## Plan Review

Check:

- Plan source: lightweight checklist or readable durable artifact when required.
- Plans with three or more comparable steps use a compact table or equivalent
  scannable structure covering scope, owner, verification, and stop/replan
  conditions.
- Scope: every step traces to the goal.
- Clarification Gate: decision-critical user requirement gaps are resolved or
  the plan is `blocked-for-clarification`; missing inputs are explicit.
- Requirements mapping: each acceptance criterion maps to observed evidence or
  verification.
- Research grounding: current APIs, upstream bugs, external behavior, and
  ambiguous architecture cite evidence or explain why local evidence is enough.
- Verification: focused checks, broader checks when warranted, and Expected
  Results are present.
- Required env vars, paths, execution modes, hyperparameters, configs, and
  commands are explicit; missing values stop as blockers instead of silently
  falling back.
- Expected output, guardrails, retry/stop conditions, and escalation triggers
  are explicit for delegated or goal-mode work.
- Risks, stop rules, Worker Handoff, Review Handoff, Subagent Routing, and
  Subagent Prompt Packets are adequate.
- Parallelization Gate appears before steps when dispatch would affect risk,
  cost, ownership, or review; 2+ independent material tracks have Dispatch
  Guidance, or `Dispatch Guidance: none` gives a continuity rationale.
- Required subagent dispatch either happened, records explicit user opt-out,
  records missing authorization, or records discovery-proven unavailability
  after the Subagent Tool Discovery Gate.
- Durable, high-risk, public/shared, or ambiguous plans have a Judge/fresh
  Reviewer verdict before acceptance, or are explicitly labeled `unreviewed`
  with residual risk.
- Prompt contract, context strategy, Required Output Schema, and escalation
  triggers are present for delegated non-lightweight work.

Return `revise` or `blocked` when:

- a required durable artifact is missing or unreadable;
- placeholders, ellipsis tasks, vague tests, missing Expected Results, or
  missing handoffs remain;
- unanswered human requirements could change goal, scope, acceptance,
  constraints, risk, or UX;
- a non-lightweight plan skips split before implementation steps or serializes
  independent material tracks without rationale;
- required subagent dispatch or fresh-context plan review is missing and no
  valid discovery/authorization/user-opt-out exception is recorded;
- delegated work lacks prompt packets, output schema, ownership, or escalation
  triggers;
- delegated execution has open dispatch status without blocker rationale;
- routing uses invalid platform dispatch fields, nonexistent agent types, or misleading
  inherited reasoning effort;
- protected contracts, architecture, or public behavior change outside scope.

## Execution Review

Check:

- Diff touches only planned files and necessary lines.
- Multi-requirement execution summaries expose a compact review table or
  equivalent structure mapping requirement, change, evidence, and status.
- Expected artifacts, outputs, metrics, or UI state match acceptance.
- Focused verification ran; broader validation exists when warranted.
- No hidden contract changes, brittle assumptions, or cleanup masking producer
  bugs.
- No silent fallback defaults, guessed hyperparameters, implicit path
  substitutions, symlink detours, or environment/provider switches mask missing
  required state.
- Diff and verification conform to the accepted lightweight plan or durable
  artifact.
- Actual Dispatch Log records subagent roles, native fields, model tier,
  context strategy, prompt packets, returned packets, order, file ownership,
  final status, and closure evidence when subagents were used.
- No delegated track remains `dispatched` or `returned` at review handoff.
- Worker Completion Packet for delegated work and Reviewer Verdict Packet for
  fresh review map implementation, verification, deviations, routing
  conformance, and residual risk to evidence.
- Worker evidence includes plan-step mapping, TDD or repro/root-cause
  applicability, verification command/result, and claim support.
- Reviewer evidence map ties each requirement or plan step to observed source,
  pass/fail/partial/not-reviewed disposition, issue, and required action.
- PR review records base/head or diff source plus unresolved thread IDs when
  available; CI review records failing check/log provenance and root cause.
- Re-review after `revise` records prior verdict, required fixes reviewed, fix
  evidence, remaining issues, and re-review verdict.
- Durable memory check: if current-state files changed, require a material
  delta and evidence; reject churn-only writes.
- Durable memory check: if accepted active state changed but no memory update
  or explicit `none`/`deferred` disposition appears, name the residual risk.
- Memory promotion check: candidate memory or docs graph output has direct
  evidence paths, currentness, scope, and protected data disposition before it
  becomes canonical Teamwork memory.
- Memory promotion check: external memory remains candidate memory when it is
  stale, unverifiable, duplicated, overly broad, or higher prompt cost than
  retrieval value.
- Manual smoke evidence captures source, observed behavior, and pass/fail
  result for any acceptance claim that depends on human-observed state.
- Stage-Routed Proactive Dispatch was evaluated even when the plan did not
  explicitly name every subagent track.
- Subagent Tool Discovery Gate ran before any unavailable-tool exception.
- Workspace has no unrelated edits, generated churn, or overwritten work.
- Version names, stale docs, comments, or summaries did not steer execution to
  wrong scope or early completion.

If work cannot be accepted, state the next route: research refresh, plan
revision, implementation correction, or true blocker.
