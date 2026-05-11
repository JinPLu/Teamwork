# Cursor Usage

Cursor does not consume Claude/Codex skill directories directly. This repository
therefore provides a thin project rule:

```text
.cursor/rules/run-analyze-optimize.mdc
```

Install into a Cursor project:

```bash
./install.sh cursor /path/to/project
```

The Cursor rule summarizes the router and subskill names and points back to the
router skill:

```text
skills/run-analyze-optimize/SKILL.md
```

Do not duplicate full skill bodies into Cursor-specific docs or rules.
