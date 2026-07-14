# Contributing to Teamwork

Thanks for helping improve Teamwork. Issues and pull requests are welcome for reproducible bugs, documentation gaps, platform compatibility problems, and focused workflow improvements.

Start with the [repository architecture](docs/architecture.md). It defines the
canonical source tree, generated and local sinks, dependency direction, stable
commands, and the owner for each kind of change.

## Before Opening An Issue

Include enough evidence for someone else to understand the problem:

- Teamwork version from `VERSION` and the latest relevant commit;
- platform: Codex, Cursor, or Claude Code;
- install target and profile used;
- expected behavior and observed behavior;
- the smallest reproduction, command output, or log excerpt that shows the failure;
- whether `./scripts/check-update.sh --no-fetch` reports installation drift.

Do not include credentials, private source, proprietary data, or unredacted personal information.

## Making A Change

1. Keep the change scoped to one behavior or documentation problem.
2. Update the owning `skills/*/SKILL.md` first when workflow behavior changes.
3. Keep Codex as the reference runtime and preserve Cursor and Claude Code adapter behavior unless the change explicitly targets one platform.
4. Add or update focused validation when changing installer logic, manifests, skill topology, artifact policy, evaluation gates, or platform contracts.
5. Change canonical sources rather than installed copies under `.agents/`, `.codex/`, `.cursor/`, or `.claude/`.
6. Keep generated runtime state out of commits. `docs/teamwork/` is local memory by default; tracked evaluation fixtures belong under the existing `evals/teamwork/` conventions.

## Verification

Run the repository checks before opening a pull request:

```bash
./scripts/validate.sh
python3 scripts/eval-teamwork.py --split dev
```

For installer changes, also test the exact target and profile you modified with a temporary `HOME` or another isolated path. Live-model evaluation is needed only when the change claims model-dependent behavior; see `python3 scripts/run-teamwork-live-eval.py --help`. For an explicitly authorized installed-package canary, see `python3 scripts/run-installed-teamwork-live-eval.py --help`.

Use the focused command named by the owning surface in the
[architecture change-owner map](docs/architecture.md#change-owners), then run
the repository checks above. Preserve the public command paths even when their
implementation moves into internal modules.

## Pull Requests

Describe:

- the user-visible problem and intended outcome;
- the workflow or runtime entrypoints changed;
- validation commands and observed results;
- compatibility or migration risk for existing Codex, Cursor, and Claude Code installs.

Keep commits focused on one logical change. Maintainers may ask to split unrelated behavior, release metadata, or broad cleanup into separate pull requests.

Use [GitHub Issues](https://github.com/JinPLu/Teamwork/issues) for bugs and proposals.
