# Artifact Protocol

Use this reference when a Teamwork stage may need durable memory. Keep ordinary
native-flow work lightweight; write artifacts only when a trigger below applies.

## Durable Artifact Triggers

Write or update `docs/teamwork/research/YYYY-MM-DD-<slug>.md` when research:

- will be reused outside the current answer;
- feeds a durable plan;
- supports goal-mode iteration or failure analysis;
- uses external calibration;
- refreshes assumptions after repeated failure or no evidence delta;
- justifies a non-trivial recommendation.

Write or update `docs/teamwork/plans/YYYY-MM-DD-<slug>.md` for goal-mode,
cross-turn, cross-agent, high-risk, ambiguous, public/shared behavior changes,
or explicit repository-plan requests.

Write or update `docs/teamwork/reports/YYYY-MM-DD-<slug>.md` for goal-mode
rolling attempts and for non-trivial conclusions that should survive the
conversation. Do not write reports for ordinary lightweight tasks.

## Full-Text Research Retrieval

Before new non-trivial research, search existing `docs/teamwork/research/`
with all useful keys available from the task:

- goal words and likely slug words;
- exact error messages, commands, failing tests, log fragments, or status text;
- component paths, package names, model names, API names, dependency names, and
  external entity names;
- old plan/report paths, issue IDs, PR names, experiment names, and user terms.

Use repository search first, for example:

```bash
rg -n "<goal|error|component|dependency|external-name>" docs/teamwork/research
```

If no directory exists, record that no prior research was available. Choose
exactly one disposition before continuing, and carry that disposition into
goal-mode reports when applicable:

- **none**: no research artifact is needed for this lightweight or purely local
  decision; state the local evidence boundary instead;
- **reuse**: cite the artifact and carry forward still-valid evidence;
- **update**: edit the artifact when the topic is the same but evidence,
  recommendation, or refresh triggers changed;
- **new**: create a new artifact and state why prior work is stale, different
  in scope, or contradicted by new evidence.

Goal-mode failure analysis must also search `docs/teamwork/reports/` for prior
attempts before repeating a hypothesis.

## Artifact Hygiene

Durable artifacts must not contain executable placeholders such as `<...>`,
`TODO`, `TBD`, or ellipsis tasks. Use concrete assumptions or mark the work
blocked when required inputs are missing.
