# Codex Usage

This repository exposes a router skill plus workflow subskills:

```text
skills/run-analyze-optimize/SKILL.md
skills/run-analyze-design/SKILL.md
skills/run-analyze-execute/SKILL.md
skills/run-analyze-review/SKILL.md
```

Install globally:

```bash
./install.sh codex
```

Codex plugin metadata lives in:

```text
.codex-plugin/plugin.json
```

When editing the workflow, keep the full instructions in the skill files. Do
not duplicate skill bodies into Codex-specific docs.
