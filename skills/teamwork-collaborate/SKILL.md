---
name: teamwork-collaborate
description: Use when the user explicitly wants to discuss, brainstorm, compare options, or make a material preference decision; do not use for clear execution or a single discoverable detail.
---

# Teamwork Collaborate

Root owns the conversation. Keep clear work native and activate Collaborate only
when the user wants to think together or when an unresolved preference would
materially change the result.

## Method

1. State the final goal, what is already settled, and the criteria that matter.
   Map the discussion from global structure to local choices with a concise
   Mermaid diagram or tree.
2. Identify the current stage. Ask every independent, valuable question for
   that stage in one batch; batch size follows semantic dependency, not a fixed
   count. Defer dependent questions to the next stage.
3. Develop only meaningfully different options. For each, explain the main
   benefit, cost, assumption, and consequence.
4. Resolve facts directly. Ask the user only for preferences or authority that
   cannot be discovered.
5. Recommend a direction when the evidence supports one. Record the user's
   decision and advance to the next dependent stage.
6. End with the decision, unresolved points, and the next authorized action.

Use subagents only for bounded evidence gathering or a genuinely independent
challenge. A handoff contains the objective, scope, settled constraints,
available evidence, and requested return. No fixed role or dispatch count is
required, and an unavailable optional subagent does not block the discussion.

When a durable discussion record is useful or requested, Root may ask Writer to
maintain one Markdown document for that continuing decision subject from
`references/discussion.md`. Every Writer wake-up explicitly
supplies the document kind and path, stable subject identity, authoritative
owner, owner-certified semantic delta, read-only context, and expected base.
Writer may compress, locate, deduplicate the current synthesis and pending
delta, update the current synthesis, and append dated history only. Existing
history is immutable. It never changes a user decision, recommendation,
confidence, authority, next action, or mainline. A missing field or conflict
returns a no-write exact gap. Writer unavailability or conflict does not block
the discussion; when the document itself is an explicit deliverable, only that
document delivery remains incomplete.
