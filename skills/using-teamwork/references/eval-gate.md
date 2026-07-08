# Eval Gate

The Teamwork eval harness is maintenance evidence, not a runtime role. Do not
add `teamwork-eval`, require evals for ordinary lightweight tasks, or treat
runner output as final acceptance.
The current runner validates fixtures and selected static samples; it does not
prove live Codex, Cursor, or Claude behavior.

## When Required

Require relevant eval evidence for package behavior changes: routing,
dispatch, review/update policy, artifact contracts, validation/harness behavior,
or skill wording that changes user-visible decisions. If no case applies, say
`no relevant eval case` and explain why.

Release/version claims also require a non-empty release split. Empty release
output is not release evidence.

## When Optional

Evals are optional for docs-only wording, typo fixes, local user refreshes,
one-off task execution, or package changes that do not alter Teamwork behavior.
Use judgment, but do not add process burden to ordinary user work.

## Split Rules

- Dev split: run while developing or reviewing candidate skill/harness changes.
- Release split: run only for release-intended, high-risk, or public-contract
  claims after dev evidence and validation; do not tune against release cases.
- Failing or inconclusive harness results are evidence. If root cause is unclear,
  route to `teamwork-debug` instead of guessing a fix.

## Optimizer Participation

Claim actual SkillOpt-Lite/HarnessOpt-Lite participation only for bounded
candidates with trajectory samples, baseline/treatment on the same dev cases,
explicit provider/model/config or offline mode, gate decision, rollback path,
ledger entry, validation, release audit after freeze, and fresh review. Release
split is audit-only; failures create future dev cases, not direct retuning.
Harness mutation also needs an editable allowlist plus smoke and full dev gates.

## Ledgers

Material skill or harness decisions need accepted/rejected ledger evidence. Keep
ledger entries compact and link large logs to `docs/teamwork/reports/`. Record
behavior deltas, validation/eval commands, reviewer evidence, and rejected
alternatives when they affected the outcome.
