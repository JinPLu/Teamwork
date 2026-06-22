# Artifact Protocol

Write durable artifacts only when a trigger applies. Default to lightweight native flow.

## Artifact Triggers

Write `docs/teamwork/research/YYYY-MM-DD-<slug>.md` when research will be reused, feeds a durable plan, supports goal-mode iteration, uses external calibration, or justifies a non-trivial reusable recommendation.

Write `docs/teamwork/plans/YYYY-MM-DD-<slug>.md` for goal-mode, cross-turn, cross-agent, high-risk, ambiguous, or shared behavior changes.

Write `docs/teamwork/reports/YYYY-MM-DD-<slug>.md` for goal-mode rolling attempts and non-trivial conclusions that should outlive the conversation.

## Retrieval Header

Start every durable artifact with:

```text
Artifact Type: research | plan | report
Status: active | superseded | accepted | blocked | budget-exhausted
Last Updated: YYYY-MM-DD
Search Keys: exact errors, commands, paths, components, dependencies, model/API names, issue/PR IDs, user terms
Abstract: 2-4 sentences covering the problem, conclusion, and applicability boundary.
Linked Artifacts: related paths, or none
```

Add `Index Role`, `Authority`, `Applies To`, `Supersedes`, `Superseded By`, or `Verification` only when they aid retrieval. Do not use YAML frontmatter; reserve that for skill metadata only.

## Structured Bodies

Durable artifacts favor compact tables and diagrams over long prose. Use tables
for three or more comparable facts, sources, options, attempts, decisions,
requirements, risks, or verification checks. Use Mermaid flowcharts for
multi-stage, branching, delegated, or goal-mode flows. Research artifacts should
include Source/Evidence and Option/Recommendation matrices when applicable.
Report artifacts should include Outcome, Attempt/Failure, Decision, and
Verification tables when applicable. Keep cells short and evidence-backed.

## Artifact Retrieval

Before non-trivial research, plan creation, or goal failure analysis, search `docs/teamwork/{research,plans,reports}/` with all available keys: goal words, errors, component paths, package/model names, issue/PR IDs, user terms.

Search `Search Keys` and headers first, then fall back to full-text:

```bash
rg -n "^(Search Keys|Abstract|Status):|<goal|error|component>" docs/teamwork/{research,plans,reports} 2>/dev/null || true
```

Choose one disposition before continuing:

- **none**: lightweight or purely local decision; state the local evidence boundary.
- **reuse**: cite and carry forward still-valid evidence.
- **update**: edit when topic is the same but evidence or assumptions changed.
- **new**: create when prior work is stale, out of scope, or contradicted by new evidence.

Goal-mode failure analysis must search `docs/teamwork/reports/` before repeating a hypothesis.

## Native Index

When durable project memory is relevant, read in this order when files exist:

1. `docs/teamwork/index.json`
2. `active.current` in index, else `docs/teamwork/current.md`
3. Active goal pointers in index (`active.goal`, `active.report`) for goal-mode
   and failed-goal recovery
4. Active stage pointers in index (`active.plan`, progress, report, result)
5. Linked artifact headers, then bodies as needed

Do not broad-scan historical artifacts by default. Read full bodies only when stage-justified.

### Index Schema (`schema_version: 1`)

Top-level fields: `schema_version` (integer, must be `1`), `last_updated`, `project`, `source_of_truth_order`, `ignore_globs`, `budgets`, `active`, `entries`, `profiles`, `pending` (optional, capped ≤ 5).

`budgets`: `default_max_files` (1–10), `default_max_artifact_bodies` (0–5), `header_first` (boolean).

`active` optional keys: `current`, `design`, `plan`, `progress`, `goal`, `report`, `results` (array when present). Scalar active pointers are string paths or `null` when known absent. `active.goal` may point to the active native-goal summary or report-backed goal note; `active.report` points to the rolling attempt report.

`entries` item fields: `topic`, `kind`, `title`, `status`, `currentness`, `authority`, `path`, `updated`, `summary`. Optional: `applies_to`, `linked`, `evidence_paths`, `supersedes`, `search_keys`.

`kind` = result / progress / design / decision / plan / report / research / runbook  
`status` = active / historical / superseded / blocked / candidate / accepted  
`authority` = canonical / active-summary / supporting / candidate / historical / superseded

External memory entries use `authority: candidate` or `supporting` until a reviewed Memory Delta promotes them. At most one `entries` item with `status: active` per `topic + kind`.

## Memory Delta

Report a memory delta when durable project memory was checked, changed, or intentionally left unchanged after a material-state question:

`Memory Delta: none | current | plan | research | decision | supersede | compact | deferred`

Use `none` when checked with no state change. Omit for work that never touched durable memory. Use `deferred` only when a conflict blocks safe updates and the handoff names the blocker.

Material delta examples: changed current result/progress/blocker/next action; changed active plan or design; accepted decision added or superseded; review found current-state inconsistency.

## Memory Promotion

External memory and docs graph output is candidate context until promoted. Promote only when the claim has evidence paths, currentness, scope, and protected data review.

Subagents propose `Memory Delta Candidate` entries only; the main agent decides whether to update canonical Teamwork memory.

## Write Boundaries

Bound normal-task writes to `docs/teamwork/index.json`, `docs/teamwork/current.md`, and at most one dated artifact unless a durable trigger justifies more. `current.md` stays a compact active digest; stage artifacts hold evidence detail.
