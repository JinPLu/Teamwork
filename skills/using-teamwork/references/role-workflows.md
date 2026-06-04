# Role Workflows

Agents enforce scope and packet boundaries. Workflows below define method; do
not paste full external skill bodies into prompts. Load the deeper role
reference only when that role is actually active.

## Explorer

Use `research-protocol.md`. For web/deep research, clarify or rewrite the
question, build a Search Plan, fan out queries, prefer primary sources, run
source-audit when confidence matters, separate public/private data, and return
evidence with dissent and Citation Ledger.

## Designer

Use task-first design: define Decision Scope, constraints, success criteria,
and decision rule before options. Compare viable options in a small matrix,
record Rejected Options, and use `designer-judge-workflow.md` to adapt
`brainstorming`, `writing-plans`, `dispatching-parallel-agents`, and
`writing-skills` into constraints, option matrix, decomposition, and acceptance
implications. Default to one role/agent unless tools, permissions, model
strength, or guardrails genuinely differ.

## Judge

Review plan adequacy, not implementation details. Check requirements mapping,
evidence freshness, routing economics, protected boundaries, verification,
guardrails, stop rules, and Acceptance Gap. Use
`designer-judge-workflow.md` and `review-checks.md` for acceptance-gap
criteria. Return `accept`, `revise`, or `blocked`; do not redesign unless a
rejection requires a concrete correction.

## Worker

Execute only the accepted owned scope. Apply TDD discipline
(`test-driven-development`) for behavior changes when practical, root-cause
debugging discipline (`systematic-debugging`) for failures, staged execution
discipline (`executing-plans` / `subagent-driven-development`) for planned
work, and fresh verification discipline (`verification-before-completion`) via
`worker-workflow.md`: mode declaration, red/green or repro/root-cause evidence,
plan-step mapping, exit condition, and proof before claim. These anchors are
method cues, not auto-install or auto-load triggers.

## Reviewer

Use fresh-context review where available. Apply review request/reception
discipline (`requesting-code-review`, `receiving-code-review`): map diff to
requirements, rank issues by severity, verify evidence independently, treat
summaries as inputs, preserve dissent, and require a fix/re-review loop for
`revise`. Use `reviewer-workflow.md` for severity crosswalk, evidence map,
PR/CI provenance, feedback disposition, and re-review closure.

## Deep Judge/Reviewer Severity

Deep Judge and Deep Reviewer are high-risk variants of Judge and Reviewer, not
new conceptual roles. Use them for failed goals, destructive or credential
risk, security, public contracts, release acceptance, or repeated review
failure.
