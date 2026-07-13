# Workflow Orchestration

Use when normal stage-routed dispatch is insufficient. This is the heavyweight
exception path; ordinary work selects only the roles whose independent evidence,
ownership, or risk reduction justifies their coordination cost.

## When To Escalate

- Codebase-wide audits or migrations.
- Many-shard research or bug hunts exceeding context budget caps.
- Adversarial plan stress tests.
- Long goal work that needs resumable state.
- Repeated workflows worth saving as a runbook.

## Shape

A workflow-class run has explicit state outside the main context:

1. **Discover**: gather scope, evidence, risks, and shard boundaries.
2. **Shard**: assign independent tracks with ownership and caps.
3. **Execute**: run Worker or Explorer waves.
4. **Verify**: run commands, artifact checks, or behavior inspection.
5. **Cross-check**: use independent Reviewer/Judge agents to challenge findings.
6. **Synthesize**: produce final evidence, residual risks, and Memory Delta.

Required fields: phase plan; concurrency and ownership bounds; verification
gate; stop controls; and compact progress accounting. Use explicit token/time or
source budgets when the user, runtime, or accepted plan supplies them; otherwise
use runtime limits and no-progress stops without inventing numbers.

## Platform Mapping

- Claude Code: map to native dynamic workflows when available and approved.
- Codex: staged custom-agent waves plus durable Teamwork artifacts.
- Cursor: background `Task` waves or project runbooks.

Workflow success is never self-acceptance. Final acceptance needs direct
verification and the independent review required by the accepted risk gate.

## Goal Retry Routing

For a goal retry, preserve the Task Contract version and Goal Invariants while
the failed claim remains in scope. Dispatch only the affected stage: Debug for
an unknown-cause reproducible failure, Execute for a known fix, and Research
only for a broad evidence gap. Re-enter Plan only after an accepted scope or
Contract delta creates a new Contract version. Re-run Review only when
acceptance claims changed or the final risk gate requires it. A failed targeted
check without either condition must not replay the full workflow. Record the
evidence-backed strategy delta; stop on repeated no progress rather than
repeating the same route.
