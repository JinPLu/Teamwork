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
self-sufficient; the User Rule paste is optional. The project `AGENTS.md`
block is the minimum shared bridge. `./install.sh cursor-policy`
prints the block for a manual Settings -> Rules -> User Rules paste;
`./install.sh cursor-policy-copy` copies the same block. The
`TEAMWORK_CURSOR_GLOBAL_START` marker is what keeps a refresh an update
instead of a duplicate.

Teamwork does not treat the policy state or adapter freshness as a blocker for
Codex or ordinary project work.

## Roles and host modes

Built-in Explore, AskQuestion, Plan, and Debug handle live interaction.
Teamwork Skills add purpose-specific contracts and checkpoint documents under
`docs/teamwork/`. The adapter exposes six focused Skills and six optional
helper roles: Researcher, Challenger, Planner, Reviewer, Worker, and Writer.
Cursor installs 6 roles; Explorer and Debugger are intentionally omitted.
Cursor does not install the Debug or Goal Skills. Planner remains an optional
bounded helper, not a substitute for Cursor's Plan mode. CreatePlan and host
Plan drafts are editable candidates; they do not complete a Skill checkpoint.
User confirmation or Build is acceptance of a reusable plan; then apply the
matching Persistence contract. Batching a stage's questions through AskQuestion
is the host mapping and still does not complete a checkpoint. CreatePlan is
not Writer. Writer is the Task
helper role (`subagent_type: writer`), not a Skill; there is no
`teamwork-writer` Skill.
`.cursor/plans` remains the host editing surface; accepted reusable results
persist under `docs/teamwork/`. If this User Rule is absent, the project
`AGENTS.md` block is the minimum shared bridge.

Cursor roles pick models by job. Researcher pins `model` to Kimi K3 high for
coverage and retrieval. The other five roles pin Grok 4.6 Fast for cheap,
few-turn coding work, with role effort in the model bracket: reviewer,
planner, challenger, and worker use high; writer uses medium. Public
retrieval scores and Cursor pool prices are directional at one snapshot;
they are not a Teamwork ranking. `--profile` does not apply to Cursor; it
affects Codex and Claude agents only, and the Cursor install does not
rewrite those pins.
