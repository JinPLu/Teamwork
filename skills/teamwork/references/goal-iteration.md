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
- relevant research artifacts from the full-text retrieval protocol.

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

Append one Markdown table row after each verification/execution-review cycle.

| Iteration | Plan Artifact | Hypothesis / Attempt | Changes | Verification | Evidence Delta | Review Verdict | Research Reuse | Artifacts Read | Agent Routing | Research / Plan Decision | Next Step / Stop Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|

The report is cross-turn memory. It does not replace the durable plan, research
artifact, native goal state, review verdict, or direct verification evidence.
