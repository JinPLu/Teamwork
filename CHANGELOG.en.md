# Changelog

[中文](CHANGELOG.md)

Notable Teamwork changes, reconstructed from git history. Dates are commit
dates. Version boundaries come from `VERSION` and plugin manifest updates where
available; the repository currently has no git release tags.

## 2.6.0 - 2026-06-23

- Strengthened broad and seeded research so a user-provided article, paper, URL,
  repo, or report is treated as seed evidence instead of the research boundary.
- Consolidated AI code-quality policy around "no silent defaults or
  invariant-masking fallback" across workflow, plan, execute, debug, review, and
  subagent contracts.
- Clarified that routine reversible defaults remain allowed, while code/runtime
  defaults and fallbacks must not hide missing required values or invariants.
- Expanded review lenses and validation anchors for bounded deslop, strict
  maintainability, fail-fast checks, and prevention of `teamwork-quality` or
  `teamwork-deslop` stage sprawl.
- Mirrored the updated bootstrap safety policy in Codex, Cursor, Claude Code,
  and installer-generated global policies.

## 2.5.0 - 2026-06-22

- Hardened goal continuity workflows with stronger Goal Anchor, Replay
  Preflight, Drift Verdict, Retry Verdict, and attempt-record expectations.
- Expanded validation coverage for goal artifacts, Teamwork index templates, and
  lifecycle verdict handling.
- Added `scripts/init-project.sh` and improved project initialization defaults,
  artifact structure, and project-local install behavior.

## 2.4.1 - 2026-06-21

- Added `./install.sh cursor-policy-copy` to copy Cursor User Rules policy text
  to the clipboard.
- Updated Cursor install, init, check-update, and validation docs around the
  manual User Rules paste step.

## 2.4.0 - 2026-06-21

- Added smarter stage routing through `routing-policy.md`.
- Refined the router and stage descriptions for native, research, debug, plan,
  execute, review, goal, init, and update workflows.

## 2.3.0 - 2026-06-21

- Added the `teamwork-debug` stage for runtime diagnosis before speculative
  fixes.
- Added `debug-mode.md`, `verification-patterns.md`, and `review-lenses.md` for
  repro evidence, proof strength, strict maintainability, and deslop reviews.
- Expanded plan, execute, review, worker, and agent templates around debug
  evidence and cleanup.
- Fixed upstream remote detection in `scripts/check-update.sh`.

## 2.2.0 - 2026-06-16

- Added install freshness and readiness checks through
  `scripts/check-update.sh`.
- Added installed-version markers, `--project-root`, and broader project-local
  install support.
- Expanded multi-platform parity across Codex, Cursor, and Claude Code agents,
  policy blocks, manifests, docs, and validation.

## 2.0.0 - 2026-06-16

- Consolidated Teamwork around act-by-default routing: proceed on clear work and
  ask only for core decisions or real blockers.
- Replaced scattered subagent references with focused dispatch, contract, and
  role playbook references.
- Slimmed validation while preserving package layout, manifest, skill, memory,
  platform, and install-smoke checks.

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

- Expanded `teamwork-update` package refresh behavior and validation coverage.
- Made skills more progressive by loading focused references only when needed.
- Added research context budget rules for Explorer and deep research packets.
- Added optional docs MCP policy for current library/API documentation lookup.
- Refined question-first routing ahead of the 2.0 consolidation.

## 1.5.0 - 1.10.0 - 2026-06-05

- Strengthened durable memory policy, clarification gates, evidence-first
  fallback positioning, rule placement, and role fan-out guidance.
- Added full-feature memory and init gates plus external-memory promotion
  safeguards.
- Added fail-fast no-defaults guidance and then slimmed workflow overhead while
  preserving reviewability.

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

- Added install-time Codex model profiles with `performance-first` and
  `cost-first` modes.
- Optimized Codex custom agent model defaults and strengthened role workflows.

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

- Refined Teamwork orchestration and workflow reference structure.
- Added delegated-track lifecycle closure contracts.
- Updated Codex Worker model mapping.
- Added runtime README pointer guidance.

## 0.14.0 - 2026-06-01

- Installed a managed Teamwork global policy block into `~/.codex/AGENTS.md`.
- Made Codex standing subagent authorization portable across projects.

## 0.13.0 - 2026-05-31

- Updated Codex subagent authorization policy.

## 0.12.0 - 2026-05-28

- Added Claude Code parity with Claude plugin metadata, `CLAUDE.md`, Claude
  install targets, and Claude agent templates.
- Extended validation to cover Claude manifests, skill installs, and agent
  templates.

## 0.11.0 - 2026-05-27

- Added Cursor platform parity with `CURSOR.md`, Cursor install support, Cursor
  Task subagent mapping, and Cursor goal-mode documentation.
- Reframed docs around platform-native capabilities instead of Codex-only
  behavior.

## 0.10.0 - 2026-05-27

- Added dispatch discovery gates before declaring subagents unavailable.
- Required explicit dispatch exceptions and fresh-review labeling for
  non-lightweight acceptance paths.

## 0.9.0 - 2026-05-27

- Released the first versioned Teamwork workflow-gates package.
- Added project initialization workflow support through `teamwork-init` and
  project-init references.
- Established Codex-only Teamwork packaging with versioned metadata.
- Split workflow responsibilities into focused skills for research, planning,
  execution, review, goal iteration, init, update, and auto-routing.
- Added evidence-first goal/runtime gates, durable artifacts, and
  review-oriented acceptance behavior.
- Added and refined automatic subagent routing, including independent-track
  dispatch, packet contracts, and model-aware routing.

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

- Started as the `run-analyze-optimize` skill package.
- Refactored the original package into router subskills for research, plan,
  execute, goal, and review.
- Added goal runtime commands, evidence gates, durable plan artifacts, and Codex
  auto-routing.
- Renamed the package to Teamwork and later narrowed it to a Codex-first skill
  package before re-expanding to multi-platform support in later releases.
