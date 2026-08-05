# Teamwork Architecture

Teamwork separates model-facing behavior from implementation infrastructure so ordinary work stays fast and specialized methods remain understandable.

## Model-facing layers

### 1. Global principles

The managed policy carries only three durable principles:

1. Keep clear work native.
2. Distinguish observation, inference, unknowns, and completed work.
3. Scale verification and defenses to credible risk and the claim being made.

Host and tool permissions remain authoritative.

### 2. Routing

`SKILL.md` descriptions are the semantic routing source. `agents/openai.yaml` is UI metadata, not a second behavior contract.

The selected public methods are Collaborate, Research, Debug, Plan, Review, Goal, Init, and Update. Their number is not an architectural invariant. Local evidence routes internally to Explorer. Strict adversarial work routes to Challenger.

### 3. Skill methods

Each Skill is self-contained and uses progressive disclosure:

- metadata contains the trigger and exclusion boundary;
- `SKILL.md` contains the concise core method;
- one-level references contain only complex optional protocols.

There is no public router, generic Execute Skill, cross-Skill behavior loading, fixed dispatch count, or workflow-wide transaction ceremony.

### 4. Agent responsibilities

Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, Worker, and Writer have narrow responsibilities. Root owns Collaborate, Goal, and user dialogue. Reviewer covers both execution and plan review. Worker preserves unrelated work. Writer maintains documents without changing facts, decisions, authority, or completion.

## One live document per task

Writer creates a task document when reusable content first appears, updates it only on material semantic change, and finalizes it at the end. It selects a Discussion, Research, Debug, Plan, Review, Goal, Init, Update, or general-report body behind a minimal common envelope.

Skills state what the document must communicate. They never expose paths, locks, CAS, transactions, readback, or integrity hashes as model procedure.

## Storage and migration

Storage remains a separate safety layer. It preserves stable case identity, one current live document, original migration inputs, collision checks, monotonic revisions, atomic writes, crash recovery, idempotent migration, and rollback.

Normal readers accept only the current schema. Older project records enter through the explicit migration path, never through runtime compatibility branches. With an exact project root, Update migrates every Teamwork document, verifies the new state, and only then resumes current-schema operation; without a root it reports migration as pending.

Hashes prove byte identity, package integrity, CAS state, or provenance. They never decide routing, semantic correctness, review acceptance, or whether content is true.

## Canonical and generated surfaces

- `skills/` owns Skill behavior.
- `templates/*-agents/` owns host agent templates.
- `scripts/install/policy.sh` owns the managed global policy.
- `config/teamwork-topology.json` owns the current mechanical inventory and retired names, not behavior.
- `scripts/build-codex-plugin.py` generates `plugins/teamwork-skill/`.

Generated plugin files are never edited directly.

## Evidence lanes

Keep claims scoped to their evidence:

1. Static contracts validate tracked source and schemas.
2. Mutation tests prove important assertions can fail.
3. Installed semantic tests exercise routing and roles on Codex, Cursor, and Claude Code.
4. Disposable-write tests exercise the real live-document lifecycle in temporary projects.

A dry run proves only configuration and command shape. Required installed or write evidence that is not run blocks release readiness instead of being rewritten as success.
