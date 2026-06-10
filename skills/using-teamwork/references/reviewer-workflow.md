# Reviewer Workflow

Use for fresh-context plan or execution review. This owns Teamwork's compact
Review Request and Review Reception discipline. GitHub PR and CI helpers are
optional evidence tools, not mandatory workflow dependencies.

## Fresh Review

Reviewer is read-only by default. Treat executor, planner, CI summaries, and
tool summaries as claims until checked against source, diff, logs, tests,
artifacts, or inspected behavior. Record the reviewed diff range or target.

## Evidence Map

Map each requirement or plan step to:

- observed evidence source;
- pass, fail, partial, or not reviewed;
- issue or disposition;
- required action when failing.

Severity crosswalk: `blocker` means acceptance is unsafe or impossible;
`major` means required before proceed; `minor` means follow-up or note.

## PR And CI Inputs

For PR review, record base/head or diff source and unresolved thread IDs when
available. For CI, inspect failing check names, failing log excerpts, and root
cause before proposing fixes. Non-GitHub or unavailable CI is report-only.

## Receiving Review

When acting on review feedback, read, understand, verify, evaluate, and then
respond. Implement one actionable issue at a time with focused verification.
Push back when feedback is stale, outside scope, unsupported, or violates the
accepted plan; record the rationale.

## Re-review after `revise`

After `revise`, a later review must identify the prior verdict, required fixes
reviewed, fix evidence, remaining issues, and re-review verdict. Do not mark a
loop closed while required fixes lack evidence.
