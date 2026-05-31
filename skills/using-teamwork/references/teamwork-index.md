# Teamwork Native Index Contract

Use this contract for local runtime memory routing under `docs/teamwork/`.

## Runtime Files

- `docs/teamwork/index.json` (required, local runtime, ignored by default)
- `docs/teamwork/README.md` (required, local human entrypoint, ignored by default)
- `docs/teamwork/current.md` (recommended compact digest, ignored by default)

## Schema (`schema_version: 1`)

Top-level fields:

- `schema_version`: integer, must be `1`
- `last_updated`: `YYYY-MM-DD`
- `project`: object with `name`, `root`, `description`
- `source_of_truth_order`: non-empty array
- `ignore_globs`: array; include `.planning/**`
- `budgets`: object
- `active`: object
- `entries`: array
- `profiles`: object
- `pending`: array (optional; capped)

`budgets`:

- `default_max_files`: integer `1..10`
- `default_max_artifact_bodies`: integer `0..5`
- `header_first`: boolean, true for templates

`active`:

- Optional keys: `current`, `design`, `plan`, `progress`, `results`
- `results` must be an array when present

`entries` item:

- `topic`, `kind`, `title`, `status`, `currentness`, `authority`, `path`, `updated`, `summary`
- Optional: `applies_to`, `linked`, `evidence_paths`, `supersedes`, `search_keys`
- Known enums: `kind` = result/progress/design/decision/plan/report/research/runbook;
  `status` = active/historical/superseded/blocked/candidate/accepted;
  `currentness` = current/stale/historical/candidate;
  `authority` = canonical/active-summary/supporting/candidate/historical/superseded.

## Continuous Memory Sync

When durable project memory was checked or changed, stage exit reports a memory
delta disposition:

- `none | current | plan | research | decision | supersede | compact | deferred`

Material delta examples:

- changed current result/progress/blocker/next action
- changed active plan or design
- accepted decision added or superseded
- review found current-state inconsistency

Non-material examples:

- routine exploration with no reusable conclusion
- transient discussion with no accepted direction change
- mechanical edits without state impact

## Pressure Controls

- Pending cap: `pending` length must be `<= 5`
- Active uniqueness: at most one `entries` item with `status: "active"` per `topic + kind`
- Keep `current.md` compact; do not use it as a running log
- Prefer index/current-first reads before broad scans

## Read Discipline

- Start with `index.json`, then active pointers
- Do not broad-scan historical artifacts by default
- Read full artifact bodies only when stage-justified
