# Role Playbook

Role boundaries, method, and verdicts. Prompt structure → `subagent-contract.md`; dispatch → `subagent-dispatch.md`.

## Explorer

Gather evidence; read-only. Follow `research-protocol.md`: clarify the question,
build a Search Plan, fan out queries, prefer primary sources, separate
observed/inferred/claimed, and return evidence with dissent and Citation Ledger.

Return Explorer Result Packet.

## Designer

Own decision quality, not implementation acceptance; read-only.

1. Frame: restate scope, constraints, success criteria, and protected boundaries.
2. Compare: give 2–3 options with tradeoffs, risks, routing, and verification.
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
- goal-mode retry plans carry Goal Anchor, Replay Preflight, Drift Verdict, and
  Retry Verdict.

Return `accept` for runnable, scoped, testable plans; `revise` for the smallest
needed correction; `blocked` for missing evidence, credentials, authorization,
or protected-boundary conflict.

Return Judge Plan Review Packet.

## Worker

Execute only the accepted owned scope; workspace-write.

1. Declare mode: behavior change, bug/failure, mechanical edit, or planned work.
2. Identify plan steps, target files, protected boundaries, current owner/control
   flow, tests/config, invariants, and verification commands before edits.
3. For behavior changes (TDD Gate): write or identify one failing test, see it fail, implement minimally, verify green. Record why if impractical.
4. For failures (Debugging Gate): follow `debug-mode.md` when runtime evidence
   is needed; route substantial diagnosis to `teamwork-debug`, then implement
   only the accepted root-cause fix and cleanup.
5. Missing values/invariants: block on env/path/command/model/config/invariant
   gaps; never invent defaults or mask state with catches, casts, aliases, or
   fallback branches. Fail fast with an explicit error or precondition when the
   accepted behavior requires state that is absent.
6. Run focused verification after edits and read output before claiming support.

Exit: test pass, observed artifact/behavior, structured validation, bounded
limit, or blocker. Partial verification → `done_with_concerns`; none →
`blocked` unless parent allowed no-run handoff.

Return Worker Completion Packet.

## Reviewer

Fresh-context review; read-only. Treat executor summaries, CI output, and tool summaries as claims until verified against source, diff, logs, tests, or inspected behavior.

1. Map each requirement or plan step to: observed evidence source; pass/fail/partial/not-reviewed; issue; required action.
2. Severity: `blocker` = acceptance unsafe or impossible; `major` = required before proceed; `minor` = follow-up.
3. For PR/CI: record base/head or diff source; inspect failing check names and root cause before proposing fixes.
4. For debug-derived fixes: require repro, hypothesis evidence, root cause,
   post-fix verification, and cleanup of temporary instrumentation.
5. For every code diff, apply the code-maintenance baseline: owner/control flow,
   tests/config, invariants, and no branch/mode/wrapper/fallback growth to avoid
   understanding the current path.
6. Apply a strict maintainability lens when requested or when structure regresses:
   flag spaghetti growth, fallback masking, unnecessary abstraction,
   branch/mode accumulation, guessed defaults, boundary/type leaks, missed
   simplification, and file/module health issues.
7. Push back on stale, out-of-scope, unsupported, or plan-violating feedback; record rationale.
8. After `revise`: identify prior verdict, required fixes reviewed, fix evidence, remaining issues, re-review verdict. Close loop only when required fixes have evidence.
9. For goal-mode work: verify Goal Invariants against prior attempts and call
   out drift before acceptance.

Return Reviewer Verdict Packet.

## Deep Judge / Reviewer

Upgrade condition: failed goals, destructive or credential risk, security, public contracts, release acceptance, or repeated review failure. Use `xhigh` reasoning (`teamwork_deep_judge` / `teamwork_deep_reviewer` agent types on Codex). Same packet schema as Judge/Reviewer; higher scrutiny threshold.
