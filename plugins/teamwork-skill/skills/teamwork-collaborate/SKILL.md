---
name: teamwork-collaborate
description: Use when the user explicitly wants to discuss, brainstorm, compare options, or make a material preference decision, or when unclear intent needs guided clarification; do not use for clear execution or a single discoverable detail.
---

# Teamwork Collaborate

Root owns the conversation. Keep clear work native and activate Collaborate when
the user wants to think together, when an unresolved preference would materially
change the result, or when unclear intent needs guided clarification.

## Method

1. State the final goal, what is already settled, and the criteria that matter.
   Map the discussion from goal to stage to questions with a concise tree or
   list; use Mermaid when the option space needs that structure.
2. A stage is one dependency layer of user-owned decisions. Ask every
   independent, valuable question for that stage together and defer dependents
   later; host UI limits are not Teamwork limits.
3. Develop only meaningfully different options. For each, explain the main
   benefit, cost, assumption, and consequence.
4. Resolve facts directly. Ask the user only for preferences or authority that
   cannot be discovered.
5. Recommend a direction when the evidence supports one. Record the user's
   decision and advance to the next dependent stage. Recorded rejections and
   decisions are the mainline; research or a subagent return must not restate
   them as a new question.
6. End with the decision, unresolved points, and the next authorized action.
   The next turn on the same subject reads the discussion document's current
   synthesis first; if it cannot be read, treat that as a memory gap and do
   not reconstruct the mainline from session recall.

Use subagents only for bounded evidence gathering or a genuinely independent
challenge. Use Explorer when available; otherwise use native local search. A
handoff contains the objective, owned scope, settled user constraints, available
evidence, and requested return. Settled user constraints must include recorded
rejections and decisions, and the requested return must not change the topic.
No fixed role or dispatch count is required, and an unavailable optional
subagent does not block the discussion.

## Persistence

At each semantic checkpoint, Root asks Writer to maintain one Markdown document
for that continuing decision subject from `references/discussion.md` at
`docs/teamwork/discussions/<YYYY-MM-DD>-<slug>.md` (reuse the existing path for
the same subject identity). Checkpoints: the user records a material decision;
a stage's option set is settled; or the discussion ends with an authorized next
action that must survive the session. A checkpoint must keep user quotes
separate from the working understanding.

Every Writer wake-up explicitly supplies the document kind and path, stable
subject identity, authoritative owner, owner-certified semantic delta,
read-only context, and expected base. Writer may compress, locate, deduplicate
the current synthesis and pending delta, update the current synthesis, and
append dated history only. Existing history is immutable. It never changes a
user decision, recommendation, confidence, authority, next action, or
mainline. A missing field or conflict returns a no-write exact gap. Writer
unavailability or conflict does not block the discussion; when a checkpoint
fired, report incomplete document delivery.
