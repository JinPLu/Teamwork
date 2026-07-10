# Artifact Protocol

Durable artifacts preserve evidence or state that must outlive the current
turn. Ordinary answers, one-turn external lookups, and bounded local changes do
not create artifacts.

## Triggers

- `docs/teamwork/research/YYYY-MM-DD-<slug>.md`: reusable or cross-turn evidence,
  research feeding a durable plan/goal, or a high-risk decision record.
- `docs/teamwork/plans/YYYY-MM-DD-<slug>.md`: cross-turn, goal, high-risk,
  public/shared behavior, long delegation, or an explicit repository plan.
- `docs/teamwork/reports/YYYY-MM-DD-<slug>.md`: rolling goal attempts or a
  non-trivial result that future work must retrieve.

External calibration alone is not a write trigger. Cite it in chat unless
reuse, continuity, risk, or an accepted plan requires durable storage.

## Retrieval Header

```text
Artifact Type: research | plan | report
Status: active | superseded | accepted | blocked | budget-exhausted
Last Updated: YYYY-MM-DD
Search Keys: <terms that retrieve this evidence>
Abstract: <problem, conclusion, and applicability boundary>
Linked Artifacts: <paths or none>
```

Add authority, scope, supersession, or verification fields only when they aid
retrieval. Use prose, tables, or diagrams according to the evidence; formatting
is not an acceptance gate.

## Retrieval

When durable memory is relevant, read in this order:

1. `docs/teamwork/index.json`.
2. `active.current`, then active goal/plan/report/result pointers.
3. Linked artifact headers and abstracts.
4. Only the bodies needed for the current decision.

For non-trivial research or goal retry, search headers with goal words, errors,
component paths, dependencies/models, IDs, and user terms. Choose `none`,
`reuse`, `update`, or `new`; do not create a near-duplicate artifact merely to
record the current turn.

Goal retries read prior failed attempt evidence before repeating a hypothesis.

## Native Index Boundary

`schema_version` remains `1`. The index may contain project metadata, retrieval
budgets, active pointers, entries, profiles, and a small pending list. Entries
identify topic, kind, title, status, currentness, authority, path, update date,
and summary, with optional scope, links, evidence, supersession, and search keys.

External memory, docs graphs, and subagent memory proposals remain candidate
context until the main agent verifies evidence path, currentness, scope, and
protected-data handling.

## Memory Delta

Report a Memory Delta only after durable memory was checked and material state
changed, conflicted, or was intentionally left unchanged:

`none | current | plan | research | decision | supersede | compact | deferred`

Omit it when durable memory was not involved. `deferred` names the conflict or
blocker. Subagents may propose a candidate; only the main agent updates
canonical memory.

Normal task writes stay bounded to the index/current digest and at most one
dated artifact unless the accepted work genuinely requires more.
