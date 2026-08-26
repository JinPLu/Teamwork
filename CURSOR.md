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
copy is already present. `teamwork-debug` stays under the Claude root only, so a
Cursor session that reads both roots can still list it; that listing is not an
install for this host. The global policy is a separate step because Cursor
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
<!-- BEGIN GENERATED: kind-root -->
`docs/teamwork/<kind>/`
<!-- END GENERATED: kind-root -->
.
<!-- BEGIN GENERATED: cursor-skills -->
The adapter exposes 7 focused Skills (`teamwork-collaborate`, `teamwork-research`, `teamwork-plan`, `teamwork-review`, `teamwork-goal`, `teamwork-init`, `teamwork-update`) and 6 optional helper roles: Researcher, Challenger, Planner, Reviewer, Worker, and Writer. Cursor installs 6 roles; Explorer and Debugger are intentionally omitted.
<!-- END GENERATED: cursor-skills -->
Cursor does not install the Debug Skill; unknown-cause diagnosis uses host
Debug. Cursor does install the Goal Skill, because a host goal carries only an
objective and its active or complete state: that state is a runtime surface, not
a checkpoint, and marking it complete is not the success signal. The Skill owns
the signal, the budget, and the Persistence contract. Planner remains an
optional bounded helper, not a substitute for Cursor's Plan mode. CreatePlan
and host Plan drafts are editable candidates; they do not complete a Skill
checkpoint.
User confirmation or Build is acceptance of a reusable plan; then apply the
matching Persistence contract. Batching a stage's questions through AskQuestion
is the host mapping and still does not complete a checkpoint. CreatePlan is
not Writer. Writer is the Task
helper role (`subagent_type: writer`), not a Skill; there is no
`teamwork-writer` Skill.
`.cursor/plans` remains the host editing surface; accepted reusable results
persist under `docs/teamwork/<kind>/`. If this User Rule is absent, the project
`AGENTS.md` block is the minimum shared bridge.

Cursor roles pick models by job. Researcher pins `model` to Kimi K3 high for
coverage and retrieval. The other five roles pin Grok 4.6 Fast for cheap,
few-turn coding work, with role effort in the model bracket: reviewer,
planner, challenger, and worker use high; writer uses medium. Public
retrieval scores and Cursor pool prices are directional at one snapshot;
they are not a Teamwork ranking. `--profile` does not apply to Cursor; it
affects Codex and Claude agents only, and the Cursor install does not
rewrite those pins.
