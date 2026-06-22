# Goal Iteration

Use only for `teamwork-goal` or goal failure recovery.

## Goal Proposal
Return chat proposal when objective, verification, scope, or stops are unclear:

```text
Goal Proposal:
- Objective: <one-sentence target>
- Done Evidence: <commands, files, artifacts, or observable acceptance checks>
- Scope: <allowed files, behavior, or systems>
- Non-goals: <explicit exclusions>
- Constraints: <permissions, compatibility, cost/time, protected boundaries>
- Goal Invariants: <persistent user constraints and acceptance meaning>
- Iteration Budget: <default 3 if unspecified>
- Retry Policy: <failed verification returns to research + plan adequacy>
- Artifacts: <none | suggested paths and why>
- Suggested Subagent Routing: <split tracks or main-agent continuity reason>
- Goal Text: <concise target for platform handoff>
```

After approval: Codex calls `create_goal` with Goal Text and keeps Goal
Invariants in plan/report. Cursor/Claude Code initializes
`docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md` with `Status: active`.

## Goal Invariants
Persist across every retry, plan review, and execution review: Goal Text,
success signal, user constraints, non-goals, protected boundaries, acceptance
criteria, allowed strictness, budget, no-progress stop, blocker conditions.

## Controller Loop
```text
init invariants -> read active.goal/report + prior attempts
-> Replay Preflight on retry -> research/debug if needed -> plan
-> plan review -> execute -> verify -> execution review -> Attempt Record
+ Failure Reflection when needed -> accept / adequacy gate / stop
```

## Replay Preflight
Before retry plan or Worker dispatch after failed, partial, blocked, or
no-progress attempts:
1. Read active goal/report, prior Attempt Records, latest plan/review, failed verification.
2. Name tried hypotheses, failed evidence, live constraints, and Do Not Repeat.
3. State strategy delta. If none, count no-progress and stop/escalate.
4. Preserve Goal Invariants; revise or ask on conflict.

## Research + Plan Adequacy Gate
Enter on failed verification, review `revise`/`blocked`, no-progress evidence
delta, or executor plan mismatch.

Read direct evidence first: failed output, current plan, execution review, Goal
Invariants, and rolling report rows.

Classify failure: research gap; debug gap; plan insufficiency; scope error;
over-strict blocker; implementation deviation; true blocker. True blocker =
missing credentials/resources, destructive risk, protected-boundary conflict,
budget exhaustion, or unresolvable user intent.

Refresh research/debug evidence and update the plan except for true blockers;
execute within budget only after Replay Preflight. Stop for true blockers,
exhausted budget, or repeated no-progress.

## Rolling Report
```text
docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md
```

Start with a retrieval header (`Artifact Type: report`), then append one row
after each verification/review cycle:

| Attempt | Goal Invariants Check | Hypothesis / Change | Verification / Failure | Result / Next |
|---|---|---|---|---|
| <n> | <preserved/conflict> | <change or test> | <command/artifact/check> | <pass/fail/blocked + decision> |

## Attempt Record And Failure Reflection
Attempt Record is mandatory after every cycle. Failure Reflection is mandatory
for failed, partial, blocked, or no-progress attempts: class,
evidence delta, over/under-strict risk, Do Not Repeat, and next plan constraint.
Debug rows add repro path, hypothesis, runtime evidence, root cause status,
cleanup status, and next route.

The report is cross-turn memory, not a replacement for plan, research, review, or verification evidence.

Lifecycle verdicts are `accept | revise | blocked`. `reject` is not a lifecycle verdict; use only for rejected hypotheses, options, sources, memory candidates, or data buckets, with a reason.
