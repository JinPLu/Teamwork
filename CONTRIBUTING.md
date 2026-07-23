# Contributing to Teamwork

Thanks for helping improve Teamwork. Issues and pull requests are welcome for
reproducible bugs, documentation gaps, platform compatibility problems, and
focused workflow improvements.

Start with the [repository architecture](docs/architecture.md). It defines the
canonical sources, generated and local sinks, one-way dependency rules, stable
commands, and the owner for each kind of change.

## Before opening an issue

Include enough evidence for someone else to understand the problem:

- Teamwork version from `VERSION` and the latest relevant commit;
- host: Codex, Cursor, or Claude Code;
- install target and profile used;
- expected behavior and observed behavior;
- the smallest reproduction, command output, or log excerpt that shows the
  failure;
- whether `./scripts/check-update.sh --no-fetch` reports installation drift.

Do not include credentials, private source, proprietary data, or unredacted
personal information.

## Making a change

1. Keep the change scoped to one user-visible behavior or documentation problem.
2. Update the owning `skills/<name>/SKILL.md` first when a capability changes.
   Each skill must be understandable on its own: do not move behavior into a
   shared reference, call another skill as a subroutine, or add a router to
   recreate a stage graph.
3. Keep clear authorized implementation on the host's native path. A distinct
   read-only local evidence question belongs to `teamwork-explore`; external,
   current, multi-source, or citation-backed evidence belongs to
   `teamwork-research`; unknown-cause failure belongs to `teamwork-debug`.
   `teamwork-design` owns unsettled consequential choices and
   `teamwork-plan` starts only after the controlled Design is `accepted`.
4. Keep Design bounded: use Explorer only for an unresolved local constraint and
   Research only for a named sanitized external/current claim that can change the
   decision; do not run both by default. Genuine trade-offs receive 2–3
   alternatives, and a clear safe path receives evidence and exclusions.
   Preserve the default one-challenge path. Activate adversarial Design only from
   Design's automatic gate or an explicit override; after the initial evidence
   wave, freeze its trial budget before dispatch,
   give every actual hypothesis two fresh isolated critics, require two new final
   auditors to pass, and fail closed when freshness or coverage is unproven.
   Preserve a finite decision frontier and the controlled Design v3 transaction:
   it records `acceptance: pending`, `accepted`, or `blocked`; persistence is not
   acceptance, and only `accepted` is Plan-ready. Legacy v1/v2 records are read
   as `accepted` for compatibility. Unproven freshness or coverage remains
   `pending` or becomes `blocked`, rather than erasing the durable state.
   The frontier shows a global map first, batches only independent
   material questions, and serializes dependent questions. Independent Plan Review runs only on
   user request or a named material risk gate.
5. Preserve result-first code work: change the canonical owner, reuse existing
   patterns/built-ins/suitable dependencies, add the smallest complete logic,
   and have each Worker prove its slice proportionally on the real path. Root
   integrates and seals a candidate before one independent max Review on user
   request or a named material risk gate. Combine findings into one repair batch
   and allow at most one delta recheck per candidate; Reviewer stays read-only.
6. Treat `templates/` as install-time host-agent adapters, not runtime skill
   prompts. A skill must not load a template to obtain behavior.
7. Keep Codex as the reference runtime and preserve Cursor and Claude Code
   adapter behavior unless the change explicitly targets one host.
8. Add or update focused validation when changing installer logic, manifests,
   skill topology, persistence, evaluation gates, or platform contracts. For
   persistence, keep the real generic and specialized transaction probes plus
   the six positive/negative development cases. Skill inventory must be
   discovered from canonical sources rather than duplicated as a fixed count.
9. Change canonical sources rather than installed copies under `.agents/`,
   `.codex/`, `.cursor/`, or `.claude/`.
10. Keep generated runtime state out of commits. `docs/teamwork/` is local memory
   by default; tracked evaluation fixtures belong under the established
   `evals/teamwork/` conventions.

In an initialized writable project, named Teamwork workflows persist reusable
artifacts by default; `no files`, off-record, read-only, or no-write overrides
that default. Grill, Design, and Goal use specialized transactions; Research,
Debug, Plan, Review, and mutating Init/Update use the generic artifact
transaction. Explore creates no standalone report. Ordinary clarification or
chat, one-off native work, and clear code implementation requests do not force
an extra workflow artifact.

Use Writer's simple model for standalone documents and runtime artifacts only
from a frozen bounded brief. Writer may draft, rewrite, organize, summarize,
translate, and polish, but must not research, invent or change facts, citations,
decisions, authority, status, or acceptance. Code comments, docstrings, tests,
schemas, manifests, machine config, and inline config text stay with the
implementation owner.

The public release inventory is ten skills, four skill-owned advanced
references, and nine host roles. A v3.4.2 cleanup can recognize only files the
installer proves it owns; it does not preserve Router, Execute, or legacy roles
as v4 aliases. Ordinary clarification stays conversation-only and does not
trigger Grill. A named or resumed Grill workflow and independently major
boundaries use its sole durable transaction record by default unless a negative
write override applies. Within one scope, persistence is limited to create,
semantic decision/frontier change, and close/supersede; unchanged state is a
no-op. New discussion records use `frontier` / `current_batch` state.

## Changelog style

Follow the compact 4.2/4.3 shape: one natural bold summary followed by one to
four concise, bold-led `- **Short heading.** Body` points. Substantive releases
normally use four points; small releases keep only the facts they have and never
pad the section. Keep every point focused on user outcomes: actions,
capabilities, compatibility, and material limits belong here, while maintainer
implementation, test counts, source topology, and internal thresholds do not.
Add `Upgrade action:` or `Important limit:` only when the action or boundary
materially changes what a user must do or expect. Chinese and English must keep
the same section order and point count, with equivalent facts and action/limit
presence and meaning. Historical edits may reorganize existing facts but must
not present an old event as newly occurring.

## Verification

Run the repository checks before opening a pull request:

```bash
./scripts/validate.sh
python3 scripts/eval-teamwork.py --split dev
```

For installer changes, test the exact target and profile in an isolated home.
When files or skills are removed, include a real previous-release-to-candidate
upgrade fixture; copying the candidate tree cannot prove cleanup compatibility.
Live-model evaluation is needed only for claims about model behavior. See
`python3 scripts/run-teamwork-live-eval.py --help` and, for an explicitly
authorized installed-package canary,
`python3 scripts/run-installed-teamwork-live-eval.py --help`.

Use the focused command named by the owning surface in the
[architecture change-owner map](docs/architecture.md#change-owners), then run
the repository checks above. Preserve public command paths even when their
implementation moves internally. Static source checks prove package shape, not
live routing or answer quality.

## Pull requests

Describe:

- the user-visible problem and intended outcome;
- the capability or runtime entrypoints changed;
- validation commands and observed results;
- compatibility or migration risk for existing Codex, Cursor, and Claude Code
  installations.

Keep commits focused on one logical change. Maintainers may ask to split
unrelated behavior, release metadata, or broad cleanup into separate pull
requests.

Use [GitHub Issues](https://github.com/JinPLu/Teamwork/issues) for bugs and
proposals.
