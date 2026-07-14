---
name: teamwork-init
description: Use when setting up, auditing, or slimming project agent instructions; integrating Teamwork artifacts, MCP/CodeGraph policy, AGENTS/CODEX/CURSOR/CLAUDE rules, install readiness, or reusable workflow-rule migration.
---

# Teamwork Init

Set up or slim project instructions. Retain facts, evidence, boundaries, and
acceptance checks.

Read as needed: `skills/using-teamwork/references/check-update.md` for readiness,
`workflow-contract.md` for evidence, `project-init.md` for layering/MCP, and
artifact/optional references only when triggered.

## Init Mode

The installed profile is the cross-platform default; ask only for project
overrides. `performance-first` uses Terra medium for Explorer, Sol medium for
Worker, Sol high for Designer/Judge/Reviewer, and Sol max for Deep roles on
Codex. `cost-first` uses Luna/Terra/Sol plus native low-cost adapter models.
`gpt56-high` and `gpt56-xhigh` pin Codex to Sol. `gpt56-role` and legacy
`gpt55-*` names are GPT-5.6 compatibility aliases. Record `Init Mode: global-default | performance-first | cost-first | gpt56-role | gpt56-high |
gpt56-xhigh | gpt55-high | gpt55-xhigh`. Refresh installed agents with
`./install.sh --profile <profile> all` when overrides change.

## Full Project Init Default

For setup/init, install the full setup first and report gaps after. Run
`./install.sh --project-root "<project-root>" init-project`, or do the equivalent.
It installs global/project skills, agents, policies, routing, notifications, managed files, and available CodeGraph. Project skills use Codex `.agents/skills/`, Cursor `.cursor/skills/`, and Claude Code `.claude/skills/`; `--no-notifications` opts out.
Context7/docs MCP is read-only external docs, not a project index. Routing
allows 9 threads total: one main plus eight subagents.

Ask only before external MCP/skill installation, credentials, protected server
state, destructive actions, or unresolved required values. Missing Teamwork
surfaces are installed directly. Cursor manual paste, unavailable CodeGraph CLI,
or missing Context7 are reported gaps, not stop conditions.

## Install Readiness Check

Before instruction work, run from the Teamwork checkout:

```bash
./scripts/check-update.sh --readiness --project "<project-root>"
```

When `INSTALL_READY=no`, run `NEXT`; user-level Codex installs repair
`codex-routing`. Treat project Codex, Cursor, and Claude gaps separately; readiness names missing skills, content drift, and version drift per host.
Native interaction tools are host capabilities, not Teamwork installation requirements. Use them when callable; never change user config to expose them. Restart after routing changes and report remaining gaps.

## Workflow

1. Run the Install Readiness Check; report `Install readiness:` without hard
   gating local files.
2. Run `./install.sh --project-root "<project-root>" init-project`, or create
   the same local surfaces directly when needed. Project surfaces continue even
   when the global install returns an actionable configuration failure; report
   that failure after local setup.
3. Inspect real project context: local instruction files, README guidance,
   `docs/teamwork/` artifacts, and user-provided plans.
4. Classify content as workflow, project fact, current state, appendix, or
   durable artifact memory.
5. Run the Collaboration Backbone Audit from `project-init.md`; mark each
   reusable workflow habit `keep`, `migrate`, or `add`.
6. Keep facts, required values, boundaries, protected actions, and acceptance
   checks in project instructions.
7. Move long path maps, command inventories, and historical navigation to
   appendix docs read on demand.
8. Keep volatile experiment numbers, task progress, and chat summaries out of
   `AGENTS.md`; use artifacts only when triggers apply.
9. For bootstrap policy, install managed Codex/Claude policy and Cursor agents;
   copy Cursor User Rules when possible. Project files hold only local facts,
   required values, or opt-outs. Report `Bootstrap policy:` and `Init Mode:`.
   For `CODEX_NOTIFICATIONS=review-required`, verify the exact command in
   `/hooks` and trust only `Stop` and `PermissionRequest` individually; never
   trust-all. Otherwise report the human action.
10. When Teamwork memory exists, keep a short pointer to
   `docs/teamwork/README.md`; do not inline the runtime narrative.
11. For full-setup requests, return the Capability Matrix from `project-init.md`.

## Boundaries

- Do not copy full external workflow, MCP, or project docs into project
  instructions.
- Do not replace project evidence sources with Teamwork artifacts.
- Do not alter protected planning, secrets, server state, or current experiment
  truth without evidence-backed user intent.
- Do not install external tooling without approval. Initializing repo-local
  CodeGraph is allowed when the CLI already exists; otherwise report the gap.

Return changed files, audit decisions, migration rationale, verification, and human decisions. Include `Memory Delta:` only when durable memory was checked or changed.
