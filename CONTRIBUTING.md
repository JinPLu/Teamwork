# Contributing

Keep changes small and behavior-led.

- Edit the owning `skills/*/SKILL.md` first.
- Update optional role behavior in `templates/*-agents/`.
- Keep universal principles in `policy/teamwork-global.md`.
- Preserve unknown user files in installer changes.
- Regenerate `plugins/teamwork-skill/` with
  `python3 scripts/build-codex-plugin.py`.

Run the fast local smoke:

```bash
./scripts/validate.sh
```

Only explicit release preparation uses:

```bash
./scripts/validate.sh --release
```

Universal authorization and mechanism rules belong only in
`policy/teamwork-global.md`; do not duplicate them in Skills, Agent profiles,
tests, or project adapters. Host adapter docs (`CURSOR.md`, `CLAUDE.md`,
`CODEX.md`) and install policy wrappers may name host tools. Shared policy and
Skill Persistence sections stay host-neutral.
