---
name: run-analyze-execute
description: Use when an accepted run/analyze/optimize plan should be implemented with minimal edits and focused verification.
---

# Run-Analyze Execute

Use this subskill only after a plan has been accepted. The executor implements
the plan; it does not self-declare completion.

## Preconditions

- Accepted plan from `run-analyze-design` with `mode: plan`, including root
  cause or goal, scope, sacred boundaries, and verification.
- Current workspace status is understood enough to avoid overwriting others.
- Required files, commands, credentials, and environments are available or the
  absence is recorded as a blocker.

If any precondition is missing, stop and return a blocker instead of guessing.

## Worker Pass

1. Re-read the accepted plan and relevant source.
2. State the files you intend to touch.
3. Make only the planned edits, matching existing style.
4. Keep changes minimal and producer-side. Avoid unrelated cleanup, formatting,
   renames, abstractions, or behavior changes.
5. Remove only code made unused by your own edit.
6. If new evidence invalidates the plan, stop and report the mismatch; do not
   expand scope silently.

## Verification

- Run the focused verification from the plan first.
- Add broader verification only when the plan calls for it or the edit touches
  shared/public behavior.
- Verification must cite real command output, artifact properties, or inspected
  diff evidence.
- If verification fails, compare against prior evidence and report whether the
  result is fixed, improved, unchanged, regressed, or new.

## Failure Handling

- On a plan mismatch: stop and request replanning.
- On a test failure caused by your edit: rework only the causal change.
- On unrelated failures: record them with evidence and avoid masking them.
- On sacred-boundary conflict, destructive risk, missing credentials, or budget
  exhaustion: stop and report a blocker.

## Handoff to Review

```text
Implemented:
- <path>: <change and plan step>

Verification:
- <command/check>: <result>

Deviations:
- <none or exact deviation and why it was necessary>

Failures / Blockers:
- <none or evidence>

Review Request:
- Validate diff, artifacts, tests, regressions, and acceptance criteria.
```
