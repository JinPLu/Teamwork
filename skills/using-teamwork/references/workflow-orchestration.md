# Workflow Orchestration

Use when normal stage-routed dispatch is too small for the job. This absorbs
the Claude Code dynamic-workflows pattern as a Teamwork concept without making
Claude-specific `.claude/workflows/` the core runtime.

## When To Escalate

Use workflow-class orchestration for:

- codebase-wide audits or migrations;
- many-shard research or bug hunts, including research whose context budget
  gate exceeds candidate, source, or source-class caps;
- adversarial plan stress tests;
- long goal work that needs resumable state;
- repeated workflows worth saving as a runbook.

Do not use it for ordinary non-lightweight work that fits Explorer, Designer,
Judge, Worker, and Reviewer dispatch.

## Shape

A workflow-class run has explicit state outside the main context:

1. Discover: gather scope, evidence, risks, and shard boundaries.
2. Shard: assign independent tracks with ownership and caps.
3. Execute: run Worker or Explorer waves.
4. Verify: run commands, artifact checks, or behavior inspection.
5. Cross-check: use independent Reviewer/Judge agents to challenge findings.
6. Synthesize: produce final evidence, residual risks, and Memory Delta.

Required fields:

- phase plan;
- concurrency cap and total-agent cap;
- token/time budget;
- packet/source budget and artifact path for many-shard research;
- ownership map;
- verification gate;
- stop controls;
- progress accounting: phase, agent count, elapsed time, and result summary.

## Platform Mapping

- Claude Code: may map to native dynamic workflows when available and approved.
- Codex: map to staged custom-agent waves plus durable Teamwork artifacts until
  Codex exposes an equivalent script runtime.
- Cursor: map to background `Task` waves or project runbooks.

Workflow success is never self-acceptance. Final acceptance still needs direct
verification and fresh review when available.
