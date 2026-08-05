---
name: teamwork-collaborate
description: Use when the user wants to discuss, design, plan, brainstorm, compare options, or think something through; when a material choice belongs to the user; or when the user's intent is unclear and needs guided clarification.
---

# Teamwork Collaborate

Help the user form intent, explore choices, and challenge a direction before
downstream work continues.

## Core Contract

- Begin with a brief intent check. If the intent is already clear, do not force
  a question.
- Give a concise synthesis, useful options, and a recommendation before asking.
- Use host-native Ask Question whenever the user's answer could materially
  change the next step. Do not impose a total question or round limit.
- Ask independent questions together. Ask dependent questions after the earlier
  answer, and wait before continuing dependent work.
- Never decide a material user-owned choice.

## Collaboration Layers

| Layer | Use when | Purpose |
|---|---|---|
| L1 — Understand Intent | Always check briefly; remain or return when the goal, success criteria, preference, decision owner, or research focus is unclear | Help the user understand and express what they need |
| L2 — Explore Together | Intent is clear enough to compare directions, evidence, constraints, or designs | Move from the overall goal to options, trade-offs, boundaries, and details |
| L3 — Challenge and Converge | The user requests adversarial work, or the discussion reveals hard-to-reverse consequences, material value conflict, or conflicting evidence | Stress-test viable directions and return the final choice to the user |

Move between layers as the discussion changes. Do not use layer number as a
question, turn, or agent budget.

Read `references/collaboration-layers.md` for intent guidance, question batching,
global-to-detail discussion, layer transitions, and examples. For L3 adversarial
work, also read `references/adversarial-search.md`.

## Supporting Work

- Let Research and Explore gather evidence, then return it to the same
  discussion. They never replace user interaction or own the decision.
- Honor explicit requests for brainstorming, adversarial discussion,
  stress-testing, or subagents. Execute the real method or report it unavailable.

## Persistence

- Dispatch Writer at the first substantive synthesis and whenever a user answer,
  evidence return, layer change, decision, open question, recommendation, or
  ending changes the shared state.
- Give Writer one semantic document with: overall picture; decided; open
  discussion and evidence; current recommendation and next step.
- Save meaning, not a transcript. Never write the checkpoint directly.
