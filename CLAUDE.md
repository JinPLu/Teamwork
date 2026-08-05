# Teamwork for Claude Code

Teamwork gives Claude Code focused collaboration methods without adding a generic Execute or router Skill. Clear local work stays native.

## Setup

```bash
./install.sh claude
./install.sh claude --profile cost-first
```

The installer preserves unrelated Claude Code configuration and maintains only Teamwork-owned skills, agents, hooks, and the global-policy block.

Initialize a new project's current-format context with `./install.sh --project-root /path/to/project init-project`.

## Routing

- Local inspection and clear implementation: native Claude Code.
- Discussion or unformed preference: `teamwork-collaborate`.
- Deep external multi-source research: `teamwork-research`.
- Unknown-cause failure: `teamwork-debug`.
- Clear direction needing execution steps: `teamwork-plan`.
- Stable candidate or plan: `teamwork-review`.
- Explicit persistence to a success signal: `teamwork-goal`.
- Current-format project initialization or repair: `teamwork-init`.
- Global Teamwork refresh and pre-7 project-document migration: `teamwork-update`.

The installed roles are Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, Worker, and Writer. Challenger is strict-adversarial only; Reviewer includes plan review. Teamwork defines no numeric dispatch cap.

Collaborate helps select an acceptable direction; Plan begins once that direction is selected. Neither step authorizes implementation.

Writer maintains one live document per task. Claude Code permissions and tools remain authoritative. Update migrates all Teamwork documents when given an exact project root; otherwise it reports project migration as pending.

Update owns all pre-7 document migration. After migration, Claude Code uses only the new format and has no legacy runtime reader.

## Verify

```bash
./scripts/check-update.sh --readiness
./scripts/validate.sh --full
```

Static checks cannot prove live hook delivery, host trust, authentication, model selection, or semantic Skill activation.
