# Review Checks

Use this reference for `teamwork-review` when a plan or implementation needs
evidence-based scrutiny.

## Plan Review

Check:

- Plan source: lightweight checklist or readable durable artifact when required.
- Scope: every step traces to the goal.
- Assumptions: missing inputs are explicit and safe.
- Requirements mapping: each acceptance criterion maps to observed evidence or
  verification.
- Research grounding: current APIs, upstream bugs, external behavior, and
  ambiguous architecture cite evidence or explain why local evidence is enough.
- Verification: focused checks, broader checks when warranted, and Expected
  Results are present.
- Risks, stop rules, Worker Handoff, Review Handoff, Subagent Routing, and
  Subagent Prompt Packets are adequate.
- Parallelization Gate appears before steps; 2+ independent tracks have
  Dispatch Guidance, or `Dispatch Guidance: none` gives a continuity rationale.
- Prompt contract, context strategy, Required Output Schema, and escalation
  triggers are present for delegated non-lightweight work.

Return `revise` or `blocked` when:

- a required durable artifact is missing or unreadable;
- placeholders, ellipsis tasks, vague tests, missing Expected Results, or
  missing handoffs remain;
- a non-lightweight plan skips split before implementation steps or serializes
  independent tracks without rationale;
- delegated work lacks prompt packets, output schema, ownership, or escalation
  triggers;
- routing uses invalid Codex fields, nonexistent agent types, or misleading
  inherited reasoning effort;
- protected contracts, architecture, or public behavior change outside scope.

## Execution Review

Check:

- Diff touches only planned files and necessary lines.
- Expected artifacts, outputs, metrics, or UI state match acceptance.
- Focused verification ran; broader validation exists when warranted.
- No hidden contract changes, brittle assumptions, or cleanup masking producer
  bugs.
- Diff and verification conform to the accepted lightweight plan or durable
  artifact.
- Actual Dispatch Log records subagent roles, native fields, model tier,
  context strategy, prompt packets, returned packets, order, and file ownership
  when subagents were used.
- Worker Completion Packet and Reviewer Verdict Packet map implementation,
  verification, deviations, routing conformance, and residual risk to evidence.
- Stage-Routed Proactive Dispatch was evaluated even when the plan did not
  explicitly name every subagent track.
- Workspace has no unrelated edits, generated churn, or overwritten work.
- Version names, stale docs, comments, or summaries did not steer execution to
  wrong scope or early completion.

If work cannot be accepted, state the next route: research refresh, plan
revision, implementation correction, or true blocker.
