# Teamwork Architecture

Teamwork is a small collection of optional methods around native work.

## Runtime flow

1. Root reads the user's request and the repository instructions.
2. Clear authorized work stays native.
3. A named Skill is loaded only when its public trigger matches.
4. Root may delegate a bounded, independent subtask when doing so is useful.
5. Root integrates the result, performs the authorized work, and verifies the
   outcome in proportion to the claim.

There is no router, mandatory stage chain, readiness preflight, document schema,
Case lifecycle, JSON index, migration gate, or automatic Update detour.

## Agent handoff

Every handoff uses the same five fields:

- objective;
- owned scope;
- settled user constraints;
- available evidence;
- requested return.

Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, Worker, and
Writer are focused helpers. They do not own the user dialogue. Missing agents
do not block native work. When the user specifically requires an
independent review and no independent context is available, Root labels the
review non-independent instead of pretending otherwise.

## Writer and documents

Writer is a low-cost, non-blocking recorder for reusable semantic changes. The
owner of the active method first certifies a semantic delta; Writer may clarify
its placement, deduplicate it, and compress it only literally, but cannot change
the owner's facts, choices, conclusions, authority, or completion state. Root
reviews the integrated result and confirms what enters the mainline. Writer
failure remains visible but does not block the method's primary work; when the
document itself was explicitly requested, only that delivery remains
incomplete.

One Writer may serve several Skills during its lifetime. That reuse is only
Agent-lifecycle reuse: Discussion, Research, Debug, Plan, Review, and Report
retain separate semantic owners and cannot certify changes for one another.

Each document is plain Markdown with two complementary views: a concise current
synthesis and an append-only chronological history of material semantic
deltas. The six meanings are:

- Discussion: options, trade-offs, settled choices, and open decisions;
- Research: external evidence, contradictions, synthesis, confidence, and stop
  basis;
- Debug: failure boundary, hypotheses, causal evidence, repair, and same-path
  verification;
- Plan: executable steps, owners, dependencies, verification, and stop
  conditions for a selected direction;
- Review: stable candidate, direct evidence, findings, and verdict;
- Report: reusable status, outcomes, and blockers from persistence, setup,
  update, or execution work.

The document system needs no Case, schema, JSON index, migration, readiness
state, or parallel authorization system. A document is
created or updated only for reusable content, never as a precondition for native
work.

## Sources and installation

- `skills/` owns behavior.
- `templates/*-agents/` owns optional host agent profiles.
- `policy/teamwork-global.md` is the sole owner of universal authorization and
  mechanism rules.
- `scripts/install/` owns installation mechanics.
- `plugins/teamwork-skill/` is generated from canonical sources.

The default install and Update path is Codex-only. Cursor and Claude Code remain
explicit compatibility targets.

## Verification

The default validation command checks syntax, Skill metadata, Codex profiles,
project initialization, and bundle synchronization. Release-only version and
packaging checks run only with `--release`. Tests and markers never substitute
for reading the actual result.
