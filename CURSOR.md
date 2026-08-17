# Cursor compatibility adapter

Cursor is an explicit compatibility and development target, not part of the
default Codex Update or validation path.

```bash
./install.sh cursor
./install.sh cursor-policy
```

`cursor` installs the Skills and helper roles. Invoke Skills with `/name` in
Cursor (for example `/teamwork-collaborate`); Codex uses `$name`. When both
same-named Teamwork skill copies exist under `~/.cursor/skills/` and
`~/.claude/skills/`, which copy Cursor reads is not guaranteed—keep both in
sync. `./install.sh cursor` refreshes the Claude skill root when that Teamwork
copy is already present. The global policy is a separate step because Cursor
keeps user rules in its own settings store rather than a file the installer
owns.

Privacy Mode (Legacy) blocks Cursor's User Rule API, so agent refresh is not
a usable path and the global policy block is not injected. Skills are
self-sufficient; the User Rule paste is optional. `./install.sh cursor-policy`
prints the block for a manual Settings -> Rules -> User Rules paste;
`./install.sh cursor-policy-copy` copies the same block. The
`TEAMWORK_CURSOR_GLOBAL_START` marker is what keeps a refresh an update
instead of a duplicate.

Teamwork does not treat the policy state or adapter freshness as a blocker for
Codex or ordinary project work.

## Roles and host modes

Built-in Explore, AskQuestion, Plan, and Debug handle live interaction.
Teamwork Skills add purpose-specific contracts and checkpoint documents under
`docs/teamwork/`. The adapter exposes the same focused Skills and seven
optional helper roles: Researcher, Debugger, Challenger, Planner, Reviewer,
Worker, and Writer. Cursor installs 7 roles; Explorer is intentionally
omitted. Planner and Debugger remain optional bounded helpers, not
substitutes for Cursor's Plan or Debug modes. CreatePlan and AskQuestion are
host signals that a plan was settled or a decision was recorded; they do not
complete a Skill checkpoint. Batching a stage's questions through AskQuestion
is the host mapping and still does not complete a checkpoint. CreatePlan is
not Writer. Writer is the Task
helper role (`subagent_type: writer`), not a Skill; there is no
`teamwork-writer` Skill. Prefer Writer for checkpoint writes; if Writer is
unavailable, Root writes the same Skill template and marks that Root fallback.
`.cursor/plans` and host Plan mode do not persist `docs/teamwork/`.

Roles pin no `model` field, so Cursor's default applies (`inherit` / parent
unless Task overrides). `--profile` does not apply to Cursor; it affects
Codex and Claude agents only, and the Cursor install does not rewrite agent
models.

## Project documents

After the method's user-facing result exists, Skills prefer Writer to persist
plain Markdown under `docs/teamwork/` (for example `plans/`, `debug/`,
`reviews/`) using `YYYY-MM-DD-<slug>.md` for a new subject and reusing the path
for the same stable identity. That is durable project memory, not a Case
lifecycle, document schema, JSON index, or migration gate. If Writer is
unavailable, Root writes the same template and marks Root fallback. A write
failure is visible and does not undo the completed result. Host plan or
question UI is not durable memory.
