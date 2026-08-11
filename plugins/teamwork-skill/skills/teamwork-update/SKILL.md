---
name: teamwork-update
description: Use when the user asks to inspect or repair Teamwork readiness, install or refresh its owned global surfaces, or orchestrate migration of all Teamwork documents under one exactly resolved and authorized project root; do not use for fresh project initialization, source release publication, or unrelated tools.
---

# Teamwork Update

Update is the current readiness and migration stage. It owns inspection, repair,
activation sequencing, exact migration scope, and the completion claim. Use
package-owned sources and host/tool authority; do not invent a second approval
protocol or assume the current directory is a Teamwork checkout.

## Resolve And Inspect Readiness

Resolve a trustworthy package source, using the installed plugin's runtime-root
helper or a verified checkout. From that resolved root, run
`./scripts/check-update.sh --readiness` and keep static freshness, installed
state, and live host activation as separate observations. A check-only request
writes nothing.

For an authorized install, refresh, activation, or repair, inspect the current
package contract, preserve unknown and user-owned files, apply only recognized
current settings, and rerun the same readiness inspection. Report observed
versions, baseline readiness, optional capability state, unresolved drift, and
manual action or restart still required. Do not modify credentials, arbitrary
plugins or tools, package managers, drivers, remote workloads, Git history,
tags, or releases.

When Codex notifications are enabled, report the observable trust state of the
Teamwork Stop and PermissionRequest hooks. Direct the user to review those
named hooks through the host; never recommend blanket hook trust or call them
active when trust has not been observed.

When another stage lacks a required leaf agent, Root suspends it, makes Update
the current stage, waits for readiness repair, and resumes only after the role
is observed ready. Root cannot substitute itself for the missing agent. The
sole bootstrap exception is a missing or broken Teamwork agent subsystem: Root
may directly perform only Update's readiness inspection and repair with native
host tools. This exception does not authorize another stage method, simulate
independence, or broaden effects.

For every check-only readiness inspection, Root must spawn the exact installed
Explorer through `agent_type`, request its bounded read-only evidence, and
observe a live child start before reporting readiness. Writer may record an
Update Report after that evidence but cannot substitute for Explorer. If the
exact Explorer is not observed, return the real blocker. Worker performs
authorized mechanical changes; if either required Agent is unavailable for a
reason other than the agent-subsystem bootstrap case, return the real blocker.

## Exact-Root Document Migration

Migrate only after the refreshed runtime is ready. Resolve and report one exact
project root covered by the user's authorization; an unambiguous current
workspace may be resolved without asking the user to restate an absolute path.
The only migration scope is `<resolved-project-root>/docs/teamwork/**`. Never
migrate project source, ordinary documentation, or project instructions.

Update owns activation, scope, sequence, recovery decision, and the final
migration claim. The responsibilities inside that sequence are exclusive:

- scripts perform only mechanical enumeration, path, schema, and index work;
- Writer alone reads the source meaning and transforms it into typed Discussion,
  Research, Debug, Plan, Review, and Report documents;
- Reviewer independently reads and accepts the actual migrated corpus.

Inventory every Teamwork document and prepare the package-defined external
staging and recovery copy before Writer transforms the complete set. Do not add
compatibility readers, dual formats, or mechanical preserved envelopes.
Preserve user meaning and stop rather than inventing a mapping. Validate the
staged schema, coverage, and ordinary retrieval, then require an independent
Reviewer to accept that frozen staged corpus.

Only an accepted staged corpus may cross the cutover boundary. Update invokes
the package cutover for the exact project root, reads the active
`docs/teamwork` tree back through the current runtime, and requires Reviewer to
read and accept that actual active corpus. If cutover fails before the migration
state reaches `cutover`, the helper has already restored the original tree;
Update observes that restoration and reports migration pending without calling
the phase-gated rollback command. If cutover succeeds but readback or the
post-cutover Review fails, Update invokes rollback from the prepared external
copy, observes the legacy tree restored, and reports the exact failure. It
never leaves a rejected schema-v4 corpus active or calls a staging verdict the
final migration verdict.

Counts, path checks, and schema validity cannot substitute for Writer's
semantic transformation or either Reviewer judgment. Claim completion only
when all inventoried content is transformed, cutover and real-path readback
succeed, the current runtime consumes it, and the post-cutover Review accepts
it. Retire the temporary recovery material only after that acceptance and any
applicable release operation no longer needs rollback; otherwise preserve it
and report its exact state.

Init owns only fresh context creation and never migration. Capability drift
belongs here, not in Goal or another stage.

## Codex Role Dispatch

On Codex, dispatch Explorer, Worker, Reviewer, and Writer through
`spawn_agent.agent_type` as `teamwork_explorer`, `teamwork_worker`,
`teamwork_reviewer`, and `teamwork_writer`. Use `fork_turns` set to `none` or
a bounded recent context, then observe a live child start; never silently
substitute an unavailable role.

When context is omitted or bounded, the brief must include every still-applicable
settled user constraint. A child cannot infer that a missing constraint was relaxed.

## Update Report

When readiness evidence, an applied repair, migration state, or a blocker is
material and reusable, Root assigns Writer a typed Report with kind Update. It
records the resolved package source, requested operation, observed outcome,
changed Teamwork-owned surfaces, readiness evidence, exact project root and
migration state when applicable, semantic acceptance, unresolved drift, and
manual actions. Writer must not claim unobserved readiness, activation, or
migration completion.
