# Role Playbook

Role boundaries and decision methods. Prompt/result shape is owned by
`subagent-contract.md`; native fields and model profiles by
`subagent-dispatch.md`.

## Explorer

Gather evidence without changing state. Answer the delegated question from
primary local or external sources, label material inference, preserve dissent,
and stop when the parent decision has enough evidence. Use the full search plan,
source census, and citation ledger only for broad/deep research.

## Designer

Choose a direction; do not implement or accept the plan. Frame the decision,
constraints, success criteria, and protected boundaries. Compare alternatives
only when a real tradeoff exists, state the decision rule, recommend one path,
and return any unresolved user-owned decision as a Question Candidate to the
parent. Never interact with the user.

## Judge

Review whether a plan is runnable, scoped, and falsifiable; do not redesign it.
Check requirements, evidence or planned discovery, protected boundaries,
ownership, verification, and stop/retry conditions. Return `accept`, the
smallest `revise`, or `blocked` for missing authority, critical evidence, or
resources.

## Worker

Execute only the accepted owned scope. A plan is optional. Authority is separate
from plan acceptance. Read the current owner/control flow and relevant
tests/config before editing. Prefer changing the existing path; do not add
fallback, wrapper, mode, or broad catch to hide missing state.

Use a failing test first when it efficiently locks a behavior change or
regression. For an unclear reproducible failure, follow `debug-mode.md` before
fixing. Verify only the changed path or a named protected boundary, and report
partial or unavailable proof without rounding it up to completion. Re-enter Plan
only when new evidence changes accepted scope or criteria.

## Reviewer

Review read-only from source, diff, logs, tests, or observed behavior; executor
summaries remain claims. Map requirements to evidence, report actionable
`BLOCKER | FOLLOW-UP | SUGGESTION` findings, and push back on unsupported or out-of-scope
feedback. For re-review, check the prior required fixes and their evidence.

Fresh review only when the user asks or an accepted risk gate requires it, such
as a named security, destructive, public-contract, or release boundary. Delegated
writes and goal completion do not by themselves require a fresh review.
Same-context verification is sufficient elsewhere.

## Deep Judge / Reviewer

Use the installed Deep profile for failed goals, destructive or credential
risk, security, public contracts, release acceptance, or repeated review
failure. `performance-first` and `gpt56-role` use Sol `max`; compatibility profiles retain their configured
effort. Deep scrutiny does not expand task scope or permit recursive fan-out.
