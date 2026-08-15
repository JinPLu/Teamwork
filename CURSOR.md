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

The adapter exposes the same focused Skills and eight optional helper roles. The
roles pin no model, so Cursor selects one through its own scheduling and the
install profile does not change them. The adapter creates no project document
schema, mandatory Writer workflow, or migration state.
