---
name: teamwork-init
description: Use when the user asks to create fresh project-local Teamwork instructions and an empty schema-v4 document skeleton in one named project; do not use to audit or repair existing Teamwork context, migrate documents, refresh global installation, or create task content.
---

# Teamwork Init

Init is the current fresh-project context stage. It creates only concise
project-local instructions and the empty schema-v4 Teamwork document skeleton.
Root resolves and reports the exact project root; Explorer inspects for ownership
conflicts and Worker performs an authorized creation.

## Inspect Before Creation

Read the applicable instruction hierarchy and confirm canonical owners, local
commands, source-of-truth paths, and stable boundaries from current project
evidence. Distinguish Teamwork-managed space from user-owned content and
preserve unrelated material.

Fail closed if Teamwork context or documents already exist, if ownership is
ambiguous, or if safe merging would rewrite user meaning. Init does not audit,
slim, repair, convert, or migrate an existing Teamwork installation. Root must
suspend Init and switch to Update with the exact resolved project root when
existing context needs readiness repair or document migration.

## Create Fresh Context

Give Worker only the exact new or Teamwork-owned surfaces. Create the minimal
project instruction block and the package-defined empty schema-v4 skeleton under
that project's `docs/teamwork/`. Do not create a case directory, `live.md`, a
typed task document, legacy reader, compatibility shim, or dual-read/write
path. Do not copy manuals or volatile progress into project instructions.

Re-read the created surfaces and run the nearest package-owned schema and
project-context validation. Report any activation or human action that the
tools cannot perform. Init never installs or refreshes global skills, agents,
policies, plugins, notifications, dependencies, credentials, or host settings.

Explorer and Worker are required for their assigned independent evidence and
mutation roles. Root must not imitate a missing role. Suspend Init, switch to
Update for readiness repair, wait, and resume or return the exact blocker.
Explorer creates no document; it returns evidence to Init.

## Codex Role Dispatch

On Codex, dispatch Explorer, Worker, and Writer through `spawn_agent.agent_type`
as `teamwork_explorer`, `teamwork_worker`, and `teamwork_writer`. Use `fork_turns`
set to `none` or a bounded recent context, then observe a live child start; never
silently substitute an unavailable role.

When context is omitted or bounded, the brief must include every still-applicable
settled user constraint. A child cannot infer that a missing constraint was relaxed.

Dispatch every Teamwork child with the normal `default` service tier. A parent
task's Fast setting does not authorize Fast for children; use acceleration only
when the current user explicitly applies it to those children.

A live child start proves the role is active. Do not impose an arbitrary return
deadline or replace it; wait for its terminal result unless the user interrupts
it or the host reports a terminal failure.

## Init Report

Only when the observed result, validation, ownership conflict, or blocker is
material and reusable, Root assigns Writer a typed Report with kind Init. It
records the resolved root, requested scope, observed outcome, decisive
validation, created Teamwork-owned surfaces, conflicts, and remaining action.
Writer must not invent project facts or report unapplied changes as complete.
