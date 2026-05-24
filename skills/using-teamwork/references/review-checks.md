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
- Risks, stop rules, Worker Handoff, Review Handoff, and Subagent Routing are
  adequate.
- Parallelization Gate appears before steps; 2+ independent tracks are routed,
  or `Dispatch: none` gives a continuity rationale.

Return `revise` or `blocked` when:

- a required durable artifact is missing or unreadable;
- placeholders, ellipsis tasks, vague tests, missing Expected Results, or
  missing handoffs remain;
- a non-lightweight plan skips split before implementation steps or serializes
  independent tracks without rationale;
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
- Actual subagent roles, model tier, context strategy, order, and file ownership
  match accepted routing when subagents were used.
- Workspace has no unrelated edits, generated churn, or overwritten work.
- Version names, stale docs, comments, or summaries did not steer execution to
  wrong scope or early completion.

If work cannot be accepted, state the next route: research refresh, plan
revision, implementation correction, or true blocker.
