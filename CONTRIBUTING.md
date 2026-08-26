# Contributing

Keep changes small and behavior-led.

- Edit the owning `skills/*/SKILL.md` first.
- Update optional role behavior in `templates/*-agents/`.
- Keep cross-project working rules in `policy/teamwork-global.md`.
- Repeated public facts live in `config/teamwork-facts.yaml`; after changing
  them, run `python3 scripts/render-teamwork-facts.py`.
- Preserve unknown user files in installer changes.

Run the fast local smoke:

```bash
./scripts/validate.sh
```

Only explicit release preparation uses:

```bash
./scripts/validate.sh --release
```

Cross-project working rules belong only in `policy/teamwork-global.md`; do not
duplicate them in Skills, Agent profiles, tests, or project adapters. Host
adapter docs (`CURSOR.md`, `CLAUDE.md`, `CODEX.md`) and install policy wrappers
may name host tools. Shared policy and Skill Persistence sections stay
host-neutral. Per-Skill write mechanics, quote separation, and Writer
no-write details live with their owners. `docs/architecture.md` owns the
closed kind set, path shape, and native persistence lifecycle; those
details do not belong in the global policy.
