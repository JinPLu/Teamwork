# Goal Iteration

Use this reference only for `teamwork-goal` or goal failure recovery.

## Goal Proposal

Return this chat-only proposal when objective, verification, scope, or stop rules are unclear:

```text
Goal Proposal:
- Objective: <one-sentence target>
- Done Evidence: <commands, files, artifacts, or observable acceptance checks>
- Scope: <allowed files, behavior, or systems>
- Non-goals: <explicit exclusions>
- Constraints: <permissions, compatibility, cost/time, protected boundaries>
- Iteration Budget: <default 3 if unspecified>
- Retry Policy: <failed verification returns to research + plan adequacy>
- Artifacts: <none | suggested paths and why>
- Suggested Subagent Routing: <tracks to split, or why main-agent continuity is better>
- Goal Text: <concise target for platform handoff>
```

After approval: Codex calls `create_goal` with the approved Goal Text. Cursor/Claude Code initializes `docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md` with `Status: active` and the Goal Text in the Abstract.

## Controller Loop

```text
initialize -> retrieve prior research/reports -> research/debug if needed -> plan
-> plan review -> execute -> verify -> execution review -> append report row
-> accept / research+plan refresh / stop
```

## Research + Plan Adequacy Gate

Enter when verification fails, execution review returns `revise` or `blocked`, evidence delta is no-progress, or the executor reports a plan mismatch.

Read direct evidence first: failed verification output, current durable plan, execution review findings, and rolling report rows.

Classify the failure:

- **research gap**: causes, external behavior, or prior attempts not understood
- **debug gap**: reproducible failure lacks runtime evidence, hypotheses,
  instrumentation, or post-fix repro verification
- **plan insufficiency**: missed evidence, wrong scope, or stale assumption
- **scope error**: touched wrong producer or boundary
- **over-strict blocker**: research can refine the allowed path
- **implementation deviation**: executor did not follow an otherwise valid plan
- **true blocker**: missing credentials/resources, destructive risk, sacred-boundary conflict, budget exhaustion, or unresolvable user intent

Refresh research/debug evidence and update the plan for the first five; execute
again within budget. Stop only for true blockers or exhausted budget.

## Rolling Report

```text
docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md
```

Start with a retrieval header (`Artifact Type: report`), then append one table row after each verification/review cycle:

| Attempt | Hypothesis | Verification | Result/Next |
|---|---|---|---|
| <n> | <what changed or was tested> | <command/artifact/check> | <pass/fail/blocked + decision> |

The report is cross-turn memory. It does not replace the durable plan, research artifact, review verdict, or direct verification evidence.

For debug attempts, put repro path, hypothesis tested, runtime evidence, root
cause status, cleanup status, and next route in the attempt row or adjacent note.
