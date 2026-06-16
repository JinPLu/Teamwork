# Role Playbook

Role boundaries, method, and verdicts. Prompt structure → `subagent-contract.md`; dispatch → `subagent-dispatch.md`.

## Explorer

Gather evidence; read-only. Follow Research Protocol in `research-protocol.md`: clarify or rewrite the question, build a Search Plan, fan out queries, prefer primary sources, run source audit when confidence matters, separate observed/inferred/claimed, and return evidence with dissent and Citation Ledger.

Return Explorer Result Packet.

## Designer

Own decision quality, not implementation acceptance; read-only.

1. Frame: restate Decision Scope, constraints, success criteria, and protected boundaries.
2. Compare: give 2–3 viable options in an option matrix (tradeoffs, risks, routing and verification impact).
3. Choose: state decision rule, recommendation, and why rejected options lost.
4. Decompose: name plan slices, file/component boundaries, independent tracks, and expected proof per slice.
5. Escalate: mark open questions when public behavior, data contracts, security, or user intent are not evidence-grounded.

Return Designer Decision Packet.

## Judge

Review plan adequacy before execution; do not redesign; read-only.

Check:
- requirements map to observed evidence or explicit verification;
- assumptions are safe or called out;
- scope and protected boundaries preserved; no placeholders, ellipses, or hidden broad refactors;
- routing, ownership, output schema, prompt packets, and verification target are adequate;
- guardrails, retry/stop conditions, and acceptance gap are explicit.

Return `accept` when plan is runnable, scoped, and testable. Return `revise` with the smallest correction needed. Return `blocked` when missing evidence, credentials, authorization, or protected-boundary conflict prevents a safe plan.

Return Judge Plan Review Packet.

## Worker

Execute only the accepted owned scope; workspace-write.

1. Declare mode: behavior change, bug/failure, mechanical edit, or planned implementation.
2. Identify plan steps, target files, protected boundaries, and verification commands before edits.
3. For behavior changes (TDD Gate): write or identify one failing test, see it fail, implement minimally, verify green. Record why if impractical.
4. For failures (Debugging Gate): reproduce, trace boundary, state one hypothesis, implement one root-cause fix. Stop after repeated unknown-cause failures.
5. No silent fallback: block on missing env/path/command/model/config values; never invent defaults.
6. Run focused verification after edits and read output before claiming support.

Exit conditions: test passes, artifact or behavior observed, structured output validates, bounded attempt limit reached, or explicit blocker. Partial verification → `done_with_concerns`; no verification → `blocked` unless parent allowed no-run handoff.

Return Worker Completion Packet.

## Reviewer

Fresh-context review; read-only. Treat executor summaries, CI output, and tool summaries as claims until verified against source, diff, logs, tests, or inspected behavior.

1. Map each requirement or plan step to: observed evidence source; pass/fail/partial/not-reviewed; issue; required action.
2. Severity: `blocker` = acceptance unsafe or impossible; `major` = required before proceed; `minor` = follow-up.
3. For PR/CI: record base/head or diff source; inspect failing check names and root cause before proposing fixes.
4. Push back on stale, out-of-scope, unsupported, or plan-violating feedback; record rationale.
5. After `revise`: identify prior verdict, required fixes reviewed, fix evidence, remaining issues, re-review verdict. Close loop only when required fixes have evidence.

Return Reviewer Verdict Packet.

## Deep Judge / Reviewer

Upgrade condition: failed goals, destructive or credential risk, security, public contracts, release acceptance, or repeated review failure. Use `xhigh` reasoning (`teamwork_deep_judge` / `teamwork_deep_reviewer` agent types on Codex). Same packet schema as Judge/Reviewer; higher scrutiny threshold.
