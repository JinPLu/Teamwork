---
name: teamwork-update
description: Use when the user asks to check, install, activate, repair, or refresh Teamwork's global skills, agents, routing, policy, plugin, notifications, or declared managed dependencies, and to migrate all Teamwork documents for one explicitly authorized exact project root after that global refresh; do not use for ordinary project initialization, source release publication, or unrelated tools.
---

# Teamwork Update

Check or refresh Teamwork-owned global installation surfaces. Use Explorer for
read-only discovery and Worker only for requested changes allowed by the current
host and tool authority. Do not create a second approval protocol inside the
Skill.

## Resolve The Installation

Do not assume the current directory is a Teamwork checkout. From an installed
plugin, resolve its package root with `scripts/plugin-runtime-root.py`. From a
checkout, verify the repository root. If no trustworthy source can be resolved,
report the missing source instead of guessing a download location.

## Check Or Refresh

1. Have Explorer run the resolved package's
   `scripts/check-update.sh --readiness`, adding its documented plugin flag for
   an installed plugin, and inspect recorded installation preferences,
   installed versions, owned global surfaces, and declared managed dependencies.
   Treat static freshness and live host activation as different claims.
2. For check-only requests, return observed baseline readiness, optional
   capability readiness, version drift, invalid or missing preferences, and
   manual activation actions without writing.
3. For install, update, activation, or repair requests, inspect the package's
   current `install.sh --help` contract and give Worker the exact Teamwork-owned
   surfaces and current-format preferences to apply. Reuse only choices that
   validate against the current contract; do not preserve unrecognized old
   settings as active configuration, silently enable optional dependencies, or
   overwrite unowned receipts.
4. Preserve unknown and user-owned files. Never modify credentials, arbitrary
   plugins or tools, package managers, drivers, CUDA, remote workloads, Git
   history, tags, or releases as part of Update.
5. Rerun the same readiness check after mutation. Report versions, baseline and
   optional capability status, unresolved drift, and any restart, trust,
   notification, or other human action still required. For Codex notifications,
   direct the user to `/hooks` and trust only Teamwork's `Stop` and
   `PermissionRequest` hooks.

Use only package-declared sources and verification for managed dependencies.
Do not infer success from file presence alone. An intentional optional-capability
opt-out is a valid baseline state, not a failed installation.

## Project Document Migration

Run project migration only after the global refresh and readiness validation
succeed. Require one exact project root that the user explicitly authorized for
this update. Do not infer it from the current directory, a repository checkout,
recent history, or a scan. If no exact root is available, complete the global
result and report `project migration pending`; do not touch project files.

For the authorized root:

1. Have Explorer inventory every Teamwork-owned project document and its format
   version before mutation. Include all Teamwork documents in the migration;
   do not select a convenient subset or mix formats opportunistically.
2. Have Worker run the package-owned full migration using the refreshed package.
   Preserve unrelated project content, but do not install old-format readers,
   compatibility shims, dual-read, or dual-write behavior.
3. Validate the complete new-format document set and its project routing on the
   real project path. Mark migration complete only when every Teamwork document
   in the inventory is converted and the current runtime can consume it.
4. After successful migration, run the project only on the new format. If the
   migration helper is unavailable, conversion is partial, or verification
   fails, report the exact blocker and keep the project migration pending; do
   not fall back to running old settings or data.

Update does not perform ordinary project initialization or edit unrelated
project context; use Init to create current-format context for a new project. It
also does not edit source release metadata or publish a release.

## Live Document

When Writer is used, include the resolved source, requested operation, versions,
preferences, observed and changed surfaces, readiness evidence, optional
capability state, exact project root or migration pending state, migration
inventory and verification, unresolved drift, and manual actions. Writer must
not report an unverified installation, activation, or project migration as
complete.
