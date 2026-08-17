---
name: teamwork-goal
description: Use when the user explicitly asks to persist until a verifiable result, fix until green, monitor through completion, or stay within a stated budget; do not infer persistence from difficulty.
---

# Teamwork Goal

Goal adds persistence to the underlying task; it does not add a second workflow.

## Method

1. State the concrete objective, success signal, applicable scope, and any user
   budget. A success signal is the directly observable result that shows the
   requested outcome is achieved. Example: the authorized command or user-stated
   completion condition is observed on the real path.
2. Perform the next useful action and observe the result.
3. Continue until the success signal is directly observed, the user interrupts,
   or a genuine external blocker prevents further progress.
4. Change approach when evidence invalidates the current one. Do not repeat a
   failed action without a new reason.
5. Report success with the observed evidence, or report the exact blocker and
   what would unblock it. Persist the checkpoint under Persistence before
   closeout; a host plan or question UI does not complete it.

Carry compact Invariants through every retry: the original objective, protected
constraints, and stop or budget state. After each attempt, keep an Attempt
Record with the previous result, the new reason to continue or stop, and the
current stop or budget state. These records live in the working context and,
when a checkpoint fires, in the report; they are not a workflow database.

Use subagents only when they provide useful independent or parallel work. Pass
the objective, owned scope, settled user constraints, available evidence, and
requested return. Missing optional agents, installation freshness, document
formats, and report writing never block the underlying authorized task.

Tests support the goal but do not replace the real success signal when that
signal is available.

## Persistence

Cross-chat memory lives in one Markdown document from `references/report.md`
at `docs/teamwork/reports/<YYYY-MM-DD>-<slug>.md`. Same identity means the same
continuing objective; reuse that path and name the document you read. A
different subject gets a new path.

Checkpoints: the success signal is directly observed; a genuine external
blocker stops progress; or the user interrupts after material progress worth
reusing. Keep user quotes separate from the working understanding.

Prefer Writer, a helper role with its own writing contract, not a Skill. If
Writer is unavailable or returns a no-write, Root writes the same template to
the same path and marks Root fallback in the closeout. The underlying goal
never blocks on Writer; silently skipping a fired checkpoint is a Skill
violation.
