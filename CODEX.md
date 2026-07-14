# Codex Usage

Teamwork for Codex is the reference Codex runtime profile for this open-source
skill package. Codex native capabilities—editing, shell execution, plans,
custom agents, permissions, MCP, browser tools, and review—remain the execution
layer. Teamwork helps decide when extra research, debugging, planning,
delegation, or verification will improve the result without slowing down simple
requests.

`VERSION` is the package version source of truth and should match both plugin
manifests.

## Install

User-level setup:

```bash
./install.sh codex
./install.sh codex --profile cost-first
./install.sh codex --profile gpt56-role  # compatibility alias
./install.sh codex --profile gpt56-high
./install.sh codex --profile gpt56-xhigh
./install.sh codex --profile cost-first --notifications
./install.sh codex --no-notifications
./install.sh codex-agents
./install.sh codex-policy
./install.sh all
```

These commands make Teamwork available to the current user; they do not
initialize every repository. Configure one selected repository with:

```bash
./install.sh --project-root /path/to/project project
./install.sh --project-root /path/to/project init-project
```

`project` installs project-local skills under `.agents/skills/` and agents under
`.codex/`, `.cursor/`, and `.claude/`. `init-project` performs the full setup for
that selected repository and also installs the current user's global Teamwork
surfaces. Use `./install.sh --link codex` or `./install.sh --link project` only
when developing from this checkout.

The default `performance-first` profile currently maps Explorer to
`gpt-5.6-terra/medium`, Worker to `gpt-5.6-sol/medium`,
Designer/Judge/Reviewer to `gpt-5.6-sol/high`, and Deep Judge/Reviewer to
`gpt-5.6-sol/max`. `cost-first` uses Luna, Terra, and Sol by role. The
`gpt56-high` and `gpt56-xhigh` profiles pin Codex agents to Sol; older GPT-named
profiles are compatibility aliases. These are configurable Codex adapter
mappings, not promises about every host or future runtime.

User-level `codex`, `all`, and `codex-agents` installs maintain Teamwork's
bounded custom-agent routing keys in `~/.codex/config.toml`. Roles live under a
non-reserved `teamwork` namespace, and the configured root-inclusive limit is
one main thread plus up to eight subagents. Unrelated TOML is preserved. Use
`--no-codex-routing` only when another owner manages those keys, and restart
Codex after routing changes. Project-only targets never modify user config.

Notifications are opt-in for direct Codex installs and enabled by default for
`all` and `init-project`. They cover main-turn completion and permission
requests; subagents remain silent. After installation, open the Codex CLI, run
`/hooks`, and review and trust each Teamwork hook. The installer cannot perform
that user-owned trust step.

## How To Use

Ask for the outcome in normal language. Teamwork is most useful for:

- research grounded in papers, official documentation, project files, or
  source history;
- reproducible debugging based on logs and runtime evidence;
- plans with explicit scope and verification;
- implementation of an accepted plan or known root-cause fix;
- fresh review for unsupported completion claims, risky fallbacks, or clutter;
- long-running work that should continue until verified or genuinely blocked.

Small facts, tiny edits, and obvious local fixes stay on Codex's native fast
path. Explicitly ask to be questioned, challenged, or “grilled” to activate
`grill-me`; otherwise Teamwork asks only when required input or a material
user-owned decision cannot be discovered safely.

Codex Plan mode and `teamwork-plan` share one planning path: Codex owns the host
UI and plan state, while Teamwork grounds scope, required values, and
verification in evidence. Plan confirmation does not authorize implementation.

Use `teamwork-init` to set up one repository, align its project instructions,
or add the optional Teamwork work-record and CodeGraph entrypoints. It targets
the selected repository rather than changing every project for the user.

## Subagents And Goals

Codex custom agents are useful only for independent work that benefits from
separation or fresh context. The root agent remains responsible for scope,
integration, user communication, verification, and the final response. Current
dispatch behavior is documented in
`skills/using-teamwork/references/subagent-dispatch.md`.

Use native Codex goal state when the user explicitly requests it or accepts a
goal proposal. Numeric budgets must come from the user or runtime; Teamwork does
not invent one.

## Evidence, Limits, And Updates

Teamwork relies on sources, repository files, configuration, tests, logs,
diffs, screenshots, and review evidence. It does not enable platform tools,
change permission policy, configure MCP or browsers, or prove model behavior by
installation alone. Host-native structured question input is used only when
the current runtime exposes it; concise text remains the fallback.

Use `teamwork-update` to refresh installed Teamwork surfaces from this checkout.
Refreshing a user's installation is separate from publishing a new Teamwork
version; maintainer release policy lives in the root `AGENTS.md`.

Useful checks:

```bash
./scripts/check-update.sh --project /path/to/project
python3 scripts/check-codex-routing.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_live_eval_runner.py
./scripts/validate.sh
```

`check-codex-routing.py` validates static routing compatibility without making
model calls. It does not replace a live spawn check after a Codex upgrade.
