# Teamwork for Cursor

Teamwork helps Cursor research unfamiliar code, diagnose failures, plan changes,
implement scoped work, review results, and keep long-running tasks grounded in
evidence. Cursor still controls editing, shell commands, MCP and browser tools,
permissions, and the model that does the work.

## Quick setup

From this checkout, install Teamwork for every supported platform:

```bash
./install.sh all
```

For Cursor only, use:

```bash
./install.sh cursor
```

Cursor stores User Rules in its own settings, so one manual step is required:

```bash
./install.sh cursor-policy-copy
```

Paste the copied block into **Cursor Settings -> Rules -> User Rules**. If
clipboard copying is unavailable, run `./install.sh cursor-policy` and copy the
printed block. The installer cannot complete or verify this Cursor setting.

The default `performance-first` profile balances everyday work with deeper
review. To favor lower-cost model choices, install with:

```bash
./install.sh cursor --profile cost-first
```

Run `./install.sh --help` to see the advanced profiles. Use `--link` only when
you want an installation to track this checkout during Teamwork development.

## Initialize a project

Set up Teamwork context for a repository with:

```bash
./install.sh --project-root /path/to/project init-project
```

This refreshes the current user's global Teamwork installation, then adds the
selected repository's project instructions, work-record entrypoints, and
CodeGraph context when available. It does not copy Teamwork skills or agents
into the repository.

## Everyday use

Ask Cursor for the outcome you want in ordinary language. For example:

- “Research how authentication works here and cite the relevant code.”
- “Diagnose why this test started failing.”
- “Plan the migration, but don't change files yet.”
- “Implement this change and verify the affected path.”
- “Review this diff for correctness and missing evidence.”
- “Keep working until the named checks pass.”

Teamwork can select research, debugging, planning, execution, review, or
long-running goal guidance from your request. Selection depends on Cursor and
the active model; explicitly name a skill when exact selection matters. Small
edits and simple questions can stay on Cursor's native path.

Replies lead with the conclusion; technical detail appears only when it helps
or you ask.

A plan helps settle scope and choices, but accepting one does not authorize file
changes. Say clearly when you want Cursor to implement, edit, run commands, or
make another external change. If you ask to be challenged, questioned, or
“grilled” before action, Teamwork can use its question-first workflow.

## Agents and continuity

The installer adds Cursor custom agents for focused exploration, implementation,
design, review, and deeper scrutiny. Teamwork may also use Cursor `Task`
subagents when independent work benefits from separate context. The main agent
remains responsible for scope, integrating the results, and explaining the
outcome plainly; subagents are not required for routine work.

When useful and authorized, Teamwork can save one compact summary of the goal,
settled choices, open question, key evidence, and continue point. Ordinary
requests do not need one.

## Updates and troubleshooting

Check whether the global installation is ready:

```bash
./scripts/check-update.sh --readiness
```

Use `teamwork-update` for guided global refreshes, or refresh explicitly with:

```bash
./install.sh all
```

Use `teamwork-init` when the issue is one repository's instructions or context.
If readiness still reports `cursor-policy-manual`, rerun
`./install.sh cursor-policy-copy` and paste the result into Cursor User Rules;
that manual action cannot be detected automatically.

Teamwork does not override Cursor permissions, MCP, browser, test settings, or
interaction UI. It will not invent paths, ports, credentials, models, commands,
or execution modes that are absent from your request or project evidence.
Natural-language skill selection also cannot be guaranteed. Cursor notification
sounds are intentionally not installed because its local hook path has not been
live-verified.
