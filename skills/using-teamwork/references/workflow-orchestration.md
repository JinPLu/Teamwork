# Workflow Orchestration

Use when normal stage-routed dispatch is insufficient. This is the heavyweight exception path; ordinary non-lightweight work uses Explorer, Designer, Judge, Worker, and Reviewer from `subagent-dispatch.md`.

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

Required fields: phase plan; concurrency cap and total-agent cap; token/time budget; packet/source budget and artifact path for many-shard research; ownership map; verification gate; stop controls; progress accounting (phase, agent count, elapsed time, result summary).

## Platform Mapping

- Claude Code: map to native dynamic workflows when available and approved.
- Codex: staged custom-agent waves plus durable Teamwork artifacts.
- Cursor: background `Task` waves or project runbooks.

Workflow success is never self-acceptance. Final acceptance still needs direct verification and fresh review.
