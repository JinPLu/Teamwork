# Artifact Protocol

Use this reference when a Teamwork stage may need durable memory. Keep ordinary
native-flow work lightweight; write artifacts only when a trigger below applies.

## Durable Artifact Triggers

Write or update `docs/teamwork/research/YYYY-MM-DD-<slug>.md` when research:

- will be reused outside the current answer;
- feeds a durable plan;
- supports goal-mode iteration or failure analysis;
- uses external calibration for a durable decision or reusable recommendation;
- refreshes assumptions after repeated failure or no evidence delta;
- justifies a non-trivial recommendation that should survive this conversation.

Write or update `docs/teamwork/plans/YYYY-MM-DD-<slug>.md` for goal-mode,
cross-turn, cross-agent, high-risk, ambiguous, public/shared behavior changes,
or explicit repository-plan requests.

Write or update `docs/teamwork/reports/YYYY-MM-DD-<slug>.md` for goal-mode
rolling attempts and for non-trivial conclusions that should survive the
conversation. Do not write reports for ordinary lightweight tasks.

## Retrieval Header

Start every durable artifact with a compact retrieval header before the body:

```text
Artifact Type: research | plan | report
Status: active | superseded | accepted | blocked | budget-exhausted
Last Updated: YYYY-MM-DD
Search Keys: exact errors, commands, paths, components, dependencies, model/API
names, issue/PR IDs, user terms
Abstract: 2-4 sentences covering the problem, conclusion, and applicability
boundary. This summary helps retrieval; it is not completion evidence.
Linked Artifacts: related research, plan, or report paths, or none
```

Use concrete values. Do not use YAML frontmatter for artifacts; reserve YAML
frontmatter for skill metadata only.

When an artifact participates in `docs/teamwork/index.json` or supersession,
add only the optional fields that help retrieval: `Index Role`, `Authority`,
`Applies To`, `Supersedes`, `Superseded By`, and `Verification`.

## Artifact Retrieval

Before new non-trivial research, plan creation, or goal failure analysis,
search existing `docs/teamwork/{research,plans,reports}/` with all useful keys
available from the task:

- goal words and likely slug words;
- exact error messages, commands, failing tests, log fragments, or status text;
- component paths, package names, model names, API names, dependency names, and
  external entity names;
- old plan/report paths, issue IDs, PR names, experiment names, and user terms.

Search retrieval headers and `Search Keys` first, then fall back to full-text
search. Use repository search, for example:

```bash
rg -n "^(Artifact Type|Status|Search Keys|Abstract|Linked Artifacts):|<goal|error|component|dependency|external-name>" docs/teamwork/{research,plans,reports} 2>/dev/null || true
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

## Research Artifact Sections

After the Retrieval Header, research artifacts should stay compact and include:
question, assumptions, local evidence, external evidence when used, options,
recommendation, dissent/risks, refresh triggers, and handoff target. Prefer
summaries plus citations over pasted logs.

For broad research, artifacts also own the source census, selected-source table,
rejected-source rationale, option or model matrix, contradiction notes,
and citation ledger overflow. Chat and subagent packets should link the
artifact and summarize only decision-relevant evidence; raw transcripts,
search-result dumps, and copied source bodies do not belong in artifacts unless
they are short, essential, and cited.

## Artifact Hygiene

Durable artifacts must not contain executable placeholders such as `<...>`,
`TODO`, `TBD`, or ellipsis tasks. Use concrete assumptions or mark the work
blocked when required inputs are missing.

## Native Index And Current-State Routing

When durable project memory is relevant, use this lookup order when files exist:

1. `docs/teamwork/index.json`
2. `active.current` in index, else `docs/teamwork/current.md`
3. active stage pointer(s) in index (`active.plan`, progress/report/result)
4. linked artifact headers, then specific bodies as needed

Lightweight native-flow tasks, short-lived chat advice, and clear one-turn
Teamwork work stay artifact-free even when they cite local evidence or public
docs.

## Memory Delta

Report a memory delta when durable project memory was checked, changed, or
intentionally left unchanged after a material-state question:

`Memory Delta: none | current | plan | research | decision | supersede | compact | deferred`

Use `none` when memory was checked and no durable project state changed. Omit
the line for work that never touched durable memory. Use `deferred` only when a
conflict blocks safe current-state updates and the handoff states the blocker.

## External Memory Promotion Gate

External memory, long-term memory, and docs graph recall are memory candidate
context until promoted. They cannot override source, tests, configs, current
artifacts, or direct tool evidence.

Promote only when the claim has evidence paths, currentness, scope, protected
data review, and a material Memory Delta reason. Subagents may propose a
`Memory Delta Candidate`; the main agent decides whether to update canonical
Teamwork memory.

## Current-State Write Boundaries

- Do not require artifacts for lightweight native-flow tasks.
- Keep normal-task current-state writes bounded to
  `docs/teamwork/index.json`, `docs/teamwork/current.md`, and at most one dated
  artifact unless a durable trigger justifies more.
- Stage artifacts hold evidence detail; `current.md` remains a compact active
  digest.
