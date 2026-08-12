# Teamwork

Teamwork is a small set of collaboration Skills for Codex. Its default is
simple: **do clear, authorized work directly; load a specialized method only
when the request matches its trigger.**

Teamwork no longer maintains a Router, mandatory stage chain, Cases, a project
document schema, Writer, global readiness gate, or version preflight.

## Runtime flow

```text
User request
  → Root decides whether a specialized Skill applies
  → Optional: delegate an independent, bounded subtask
  → Root integrates and performs the authorized work
  → Verify the real outcome in proportion to the claim
```

Every subagent handoff has five fields: objective, owned scope, settled user
constraints, available evidence, and requested return.

An unavailable Agent does not trigger Update and does not block work that Root
can perform directly. If the user explicitly requires independent review but
the host cannot provide independent context, Root labels the review
non-independent instead of pretending otherwise.

## Skills

| Request | Skill | Result |
|---|---|---|
| Discuss or compare directions | `$teamwork-collaborate` | Options, trade-offs, and a decision |
| Deep external investigation | `$teamwork-research` | Multi-source, claim-level synthesis |
| Unknown-cause failure | `$teamwork-debug` | Cause first, authorized repair second |
| Plan a selected direction | `$teamwork-plan` | Executable work and verification links |
| Review a stable candidate | `$teamwork-review` | Evidence-backed verdict and findings |
| Persist to a success signal | `$teamwork-goal` | Continued progress on the original task |
| Add project instructions | `$teamwork-init` | One small managed AGENTS.md block |
| Inspect or refresh installation | `$teamwork-update` | Codex install state by default |

Ordinary edits, local inspection, narrow lookups, and known-cause fixes need no
Teamwork preflight.

## Agent behavior

Seven optional internal roles remain: Researcher, Explorer, Debugger,
Challenger, Planner, Reviewer, and Worker.

- Root owns user dialogue, integration, and the final result.
- Agents stay inside the supplied brief.
- A failed subtask affects that subtask, not the whole workflow.
- Reviewer is read-only and never implements its own findings.

## Installation

Codex Marketplace is the default:

```text
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Then run `$teamwork-update` in a new task. For checkout development:

```bash
./install.sh --help
```

`update` refreshes Codex only. Cursor and Claude Code remain explicit
compatibility-development targets and never block Codex work.

## Project setup

```bash
./install.sh --project-root /absolute/project/path init-project
```

This idempotently adds or refreshes one managed block in `AGENTS.md`. It creates
no `docs/teamwork`, Case, index, schema, migration state, or runtime files.

## Verification

```bash
./scripts/validate.sh
```

The default smoke covers syntax, Skill metadata, Codex profiles, project init,
non-blocking readiness, and generated bundle synchronization. Explicit release
preparation adds packaging version checks:

```bash
./scripts/validate.sh --release
```

Install state is informational:

```bash
./scripts/check-update.sh --readiness
```

It exits successfully and never authorizes or blocks another task.

## Development rules

- `skills/` is the behavior source of truth.
- `templates/*-agents/` contains optional role profiles.
- `policy/teamwork-global.md` contains the minimal global principles.
- `plugins/teamwork-skill/` is generated from canonical sources.
- Unknown or user-owned install files are not overwritten.
- Universal authorization and mechanism rules live only in
  `policy/teamwork-global.md`.

License: [MIT](LICENSE)
