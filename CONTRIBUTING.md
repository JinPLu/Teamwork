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
   `teamwork-plan` starts only after a direction is selected.
4. Keep Design bounded: use Explorer only for an unresolved local constraint and
   Research only for a named sanitized external/current claim that can change the
   decision; do not run both by default. Genuine trade-offs receive 2–3
   alternatives, and a clear safe path receives evidence and exclusions.
   Preserve the default one-challenge path. Activate adversarial Design only from
   Design-qualified explicit intent; freeze its trial budget before dispatch,
   give every actual hypothesis two fresh isolated critics, require two new final
   auditors to pass, and fail closed when freshness or coverage is unproven.
   Preserve a finite decision frontier and the controlled durable Design artifact
   before Plan. The frontier shows a global map first, batches only independent
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
   skill topology, persistence, evaluation gates, or platform contracts. Skill
   inventory must be discovered from canonical sources rather than duplicated
   as a fixed count.
9. Change canonical sources rather than installed copies under `.agents/`,
   `.codex/`, `.cursor/`, or `.claude/`.
10. Keep generated runtime state out of commits. `docs/teamwork/` is local memory
   by default; tracked evaluation fixtures belong under the established
   `evals/teamwork/` conventions.

The public release inventory is ten skills, three skill-owned advanced
references, and eight host roles. A v3.4.2 cleanup can recognize only files the
installer proves it owns; it does not preserve Router, Execute, or legacy roles
as v4 aliases. An ordinary question-first Grill stays conversation-only;
explicit persistence and independently major boundaries use its sole durable
transaction record. Within one scope, persistence is limited to create,
semantic decision/frontier change, and close/supersede; unchanged state is a
no-op. New discussion records use `frontier` / `current_batch` state.

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
