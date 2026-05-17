# Cursor Usage

Cursor does not consume Claude/Codex skill directories directly. This repository
therefore provides a thin project rule:

```text
.cursor/rules/teamwork.mdc
```

Install into a Cursor project:

```bash
./install.sh cursor /path/to/project
```

The Cursor rule summarizes the router and subskill names and points back to the
router skill:

```text
skills/teamwork/SKILL.md
skills/teamwork-goal/SKILL.md
skills/teamwork-research/SKILL.md
skills/teamwork-plan/SKILL.md
```

Use the skill files as the behavioral source of truth, including evidence
classification, review discipline, and cost/subagent constraints.

Do not duplicate full skill bodies into Cursor-specific docs or rules.
