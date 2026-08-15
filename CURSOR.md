# Cursor compatibility adapter

Cursor is an explicit compatibility and development target, not part of the
default Codex Update or validation path.

```bash
./install.sh cursor
./install.sh cursor-policy
```

`cursor` installs the Skills and helper roles. The global policy is a separate
step because Cursor keeps user rules in its own settings store rather than a
file the installer owns.

Apply the printed block as one Cursor user rule. A Cursor Agent can do this
through Cursor's user-rule API: list the existing rules, update the rule whose
content carries the `TEAMWORK_CURSOR_GLOBAL_START` marker or add it when no such
rule exists, then list again and compare the stored content against
`./install.sh cursor-policy`. The marker is what keeps a refresh an update
instead of a duplicate. Without an agent, `./install.sh cursor-policy-copy`
copies the same block for a manual Settings -> Rules -> User Rules paste.

Teamwork does not treat the policy state or adapter freshness as a blocker for
Codex or ordinary project work.

## Roles and host modes

Built-in Explore, AskQuestion, Plan, and Debug handle live interaction.
Teamwork Skills add purpose-specific contracts and checkpoint documents under
`docs/teamwork/`. The adapter exposes the same focused Skills and seven
optional helper roles: Researcher, Debugger, Challenger, Planner, Reviewer,
Worker, and Writer. Cursor installs 7 roles; Explorer is intentionally
omitted. Planner and Debugger remain optional bounded helpers, not
substitutes for Cursor's Plan or Debug modes.

Roles pin no `model` field, so Cursor's default applies (`inherit` / parent
unless Task overrides). `--profile` does not apply to Cursor; it affects
Codex and Claude agents only, and the Cursor install does not rewrite agent
models.

## Project documents

At semantic checkpoints, Skills ask Writer to persist plain Markdown under
`docs/teamwork/` (for example `plans/`, `debug/`, `reviews/`) using
`YYYY-MM-DD-<slug>.md` for a new subject and reusing the path for the same
stable identity. That is durable project memory, not a Case lifecycle, document
schema, JSON index, or migration gate. Writer failure never blocks the primary
method; incomplete document delivery is reported when a checkpoint fired.
