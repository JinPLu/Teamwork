# Teamwork for Claude Code

Teamwork 7.1 does not officially support or release-qualify Claude Code. This retained source adapter exists for compatibility maintenance and local development only; Codex is the supported install and release-evidence path.

The adapter still gives Claude Code focused collaboration methods without adding a generic Execute or router Skill when you choose to test or maintain it. Clear local work stays native.

## Compatibility Setup

```bash
./install.sh claude
./install.sh claude --profile cost-first
```

The installer preserves unrelated Claude Code configuration and maintains only
Teamwork-owned Skills, Agents, hooks, and the managed block rendered from
`policy/teamwork-global.md`. Readiness reports static installation and observed
policy activation separately.

Initialize a new project's current-format context with `./install.sh --project-root /path/to/project init-project`.

## Routing

- Local inspection and clear implementation: native Claude Code.
- Discussion or unformed preference: `teamwork-collaborate`.
- Deep external multi-source research: `teamwork-research`.
- Unknown-cause failure: `teamwork-debug`.
- Clear direction needing execution steps: `teamwork-plan`.
- Stable candidate or plan: `teamwork-review`.
- Explicit persistence to a success signal: `teamwork-goal`.
- Fresh current-format project initialization: `teamwork-init`; use `teamwork-update` for installed-state repair.
- Global Teamwork refresh and older project-document migration, including 7.0 schema-v3 records: `teamwork-update`.

The installed roles are Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, Worker, and Writer. Challenger is strict-adversarial only; Reviewer includes plan review. Teamwork defines no numeric dispatch cap.

Collaborate helps select an acceptable direction; Plan begins once that direction is selected. Neither step authorizes implementation.

Writer is the sole semantic writer for Discussion, Research, Debug, Plan,
Review, and Report documents, all discovered through `docs/teamwork/index.json`.
Claude Code permissions and tools remain authoritative. Update migrates all
Teamwork documents when given an exact project root; otherwise it reports
project migration as pending.

Update owns older-document migration. Writer performs semantic reorganization,
scripts do mechanics, and an independent Reviewer accepts the actual migrated
corpus. After migration, Claude Code uses only schema v4 and has no legacy
runtime reader.

## Verify

```bash
./scripts/check-update.sh --readiness
./scripts/validate.sh --full
```

Structural checks cannot prove live hook delivery, host trust, authentication,
model selection, or semantic Skill behavior. Those claims require observed host
behavior or an independent Reviewer reading the actual candidate. Claude Code
results are compatibility and development signals only; they are not Teamwork
7.1 support claims or release blockers.
