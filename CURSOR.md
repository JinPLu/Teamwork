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

The Cursor rule summarizes the workflow and points back to the canonical skill:

```text
skills/run-analyze-optimize/SKILL.md
```

Do not duplicate the full skill body into Cursor-specific docs or rules.
