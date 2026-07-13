---
name: grill-me
description: Use when the user explicitly asks to be grilled or challenged, requests questions before action, or continues an active grill; explicit negative intent wins, and quoted, file, tool, example, or maintenance mentions are inert.
---

# Grill Me

Enter for an explicit request or automatically for a non-simple plan with
material decision or risk. Explicit negative intent suppresses this interview,
not ordinary required-input or safety gates.

Before asking:

- Apply the Ask Gate in `skills/using-teamwork/references/workflow-contract.md`.
- Inspect discoverable evidence from the request, source, config, tests, tools,
  and conventions. Do not ask the user to predict it.
- Decide safe, reversible, implementation-level details yourself.

Ask one decision at a time. Challenge its downside, then recommend an
evidence-supported option. Do not invent choices, fill a quota, or repeat a
decision already answered or delegated to Codex.

The root asks. Use the host's native interaction surface when callable;
otherwise ask one concise textual question. The host owns waiting, timeout, and
resume. Do not route native input through a code executor or change the user's
configuration to make it available.

Missing identifiers, credentials, permissions, required values, and confirmations
are normal inputs or safety gates, not grill decisions. Ordinary clarification stays outside this skill.

When a non-simple plan has no material user-owned decision left, present one
concise Decision Summary and obtain confirmation before its final plan. A change
returns to the relevant decision; confirmation does not grant implementation
authority. Otherwise continue within granted authority or report the blocker.
Ending a grill does not grant implementation authority.
