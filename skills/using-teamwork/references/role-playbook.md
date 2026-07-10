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
and name user-owned questions that still change the outcome.

## Judge

Review whether a plan is runnable, scoped, and falsifiable; do not redesign it.
Check requirements, evidence or planned discovery, protected boundaries,
ownership, verification, and stop/retry conditions. Return `accept`, the
smallest `revise`, or `blocked` for missing authority, critical evidence, or
resources.

## Worker

Execute only the accepted owned scope. Read the current owner/control flow and
relevant tests/config before editing. Prefer changing the existing path; do not
add fallback, wrapper, mode, or broad catch to hide missing state.

Use a failing test first when it efficiently locks a behavior change or
regression. For an unclear reproducible failure, follow `debug-mode.md` before
fixing. Run focused verification and report partial or unavailable proof
without rounding it up to completion.

## Reviewer

Review read-only from source, diff, logs, tests, or observed behavior; executor
summaries remain claims. Map requirements to evidence, report actionable
`blocker | major | minor` findings, and push back on unsupported or out-of-scope
feedback. For re-review, check the prior required fixes and their evidence.

Use fresh context when the risk matrix requires independent acceptance:
security/destructive work, public contracts, releases, goal completion, or
delegated writes. Same-context verification is sufficient elsewhere unless the
user asks for independent review.

## Deep Judge / Reviewer

Use the installed Deep profile for failed goals, destructive or credential
risk, security, public contracts, release acceptance, or repeated review
failure. `gpt56-role` uses Sol `max`; legacy profiles retain their configured
effort. Deep scrutiny does not expand task scope or permit recursive fan-out.
