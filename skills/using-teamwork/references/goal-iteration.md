# Goal Iteration

Use this reference only for `teamwork-goal` or goal failure recovery.

## Goal Input Contract

Recommended user-facing shape:

```text
Achieve <target>; accept only with <verifiable evidence>; preserve
<constraints>; restrict scope to <files/tools/boundaries>; choose each next
iteration from <decision rule>.
```

The angle brackets are prompt guidance only. Replace them before writing any
artifact. A valid goal can still be natural language, but the controller should
extract: objective, verification evidence, boundaries, allowed tools/files, and
stop rules.

## Goal Proposal

Return this chat-only proposal before platform goal handoff when objective,
verification, scope, or stop rules are unclear:

```text
Goal Proposal:
- Objective: <one-sentence target>
- Done Evidence: <commands, files, artifacts, or observable acceptance checks>
- Scope: <allowed files, behavior, or systems>
- Non-goals: <explicit exclusions>
- Constraints: <permissions, compatibility, cost/time, protected boundaries>
- Iteration Budget: <default 3 if unspecified, or user-specified>
- Retry Policy: <failed verification returns to research + plan adequacy>
- Artifacts: <none | suggested research/plan/report paths and why>
- Suggested Subagent Routing: <tracks to split, or why main-agent continuity is better>
- Goal Text: <concise target for platform goal handoff>
```

The proposal is not a durable plan artifact, not visible progress UI, and not a
completion claim. After approval:

- Codex: call `create_goal` with the approved Goal Text.
- Cursor: initialize `docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md` with
  `Status: active` and put the Goal Text in the report Abstract.
- Claude Code: same as Cursor — no native goal surface; initialize the rolling
  report with `Status: active` and the Goal Text in the Abstract.

## Controller Loop

Use this loop for autonomous convergence:

```text
initialize -> retrieve prior research/reports -> research if needed -> plan
-> plan review -> execute -> verify -> execution review -> append report row
-> accept / research+plan refresh / stop
```

## Research + Plan Adequacy Gate

Enter this gate when verification fails, acceptance cannot be judged, execution
review returns `revise` or `blocked`, evidence delta is `no-progress`, or the
executor reports a plan mismatch.

Read direct evidence before deciding:

- failed verification command/output or missing artifact;
- current durable plan and plan SHA;
- execution review findings and deviations;
- current rolling report rows;
- relevant research, plan, and report artifacts from the artifact retrieval
  protocol.

Classify the failure:

- research gap: causes, external behavior, or prior attempts are not understood;
- plan insufficiency: the plan missed evidence, chose the wrong scope, or has a
  stale assumption;
- scope error: implementation touched the wrong producer or boundary;
- over-strict blocker: the plan stopped even though research can refine the
  allowed path;
- implementation deviation: executor did not follow an otherwise valid plan;
- true blocker: missing credentials/resources, destructive risk, sacred-boundary
  conflict, budget exhaustion, or user intent/public contract ambiguity.

When the issue is research gap, plan insufficiency, scope error, or over-strict
blocker, refresh research, update or replace the durable plan, re-record the
plan, repeat plan review, then execute again within budget. Stop only for true
blockers or exhausted budget.

## Rolling Report

Each goal keeps one report:

```text
docs/teamwork/reports/YYYY-MM-DD-<goal-slug>.md
```

Start the report with a retrieval header, then append one Markdown table row
after each verification/execution-review cycle.

```text
Artifact Type: report
Status: active | accepted | blocked | budget-exhausted
Last Updated: YYYY-MM-DD
Search Keys: exact errors, commands, paths, components, dependencies, model/API
names, issue/PR IDs, user terms
Abstract: 2-4 sentences covering the goal, current outcome, and applicability
boundary. This summary helps retrieval; it is not completion evidence.
Linked Artifacts: related research or plan paths, or none
```

| Iteration | Plan Artifact | Hypothesis / Attempt | Changes | Verification | Evidence Delta | Review Verdict | Research Reuse | Artifacts Read | Agent Routing | Research / Plan Decision | Next Step / Stop Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|

The report is cross-turn memory. It does not replace the durable plan, research
artifact, platform goal surface, review verdict, or direct verification evidence.

## Goal Output

For multi-attempt goals, prefer a compact table in the final answer before the
conclusion so humans can audit each attempt without reading the full rolling
report.

| Attempt | Hypothesis | Verification | Result | Next Step / Stop Reason |
|---|---|---|---|---|
| <n> | <what changed or was tested> | <command/artifact/check> | <pass/fail/blocked> | <decision> |

```text
Route: teamwork-goal
Reason: <one sentence tied to autonomous convergence>
Mode: goal
Platform Goal Surface: codex-native: proposed | created | continued | completed | not used
  or cursor-report | claude-report: initialized | active | accepted | blocked | budget-exhausted
Active Plan Artifact: <docs/teamwork/plans/YYYY-MM-DD-<slug>.md | none>
Rolling Report: <docs/teamwork/reports/YYYY-MM-DD-<slug>.md | none>
Iterations: <n and short summary>
Verification: <command/artifact/check and result>
Review: <plan/execution verdicts>
Completion Evidence: <requirement-to-evidence map>
Unresolved: <none or blockers>
Conclusion: accept | blocked | budget exhausted | stopped
```
