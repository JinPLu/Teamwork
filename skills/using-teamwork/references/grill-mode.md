# Grill Mode

Grill mode is a question-first interaction override, not a Teamwork stage. Use
it when the user asks to "grill me", "grill-me", "question-first",
"stress-test", "challenge my assumptions", "ask before acting", or direct
equivalents such as "先问清楚". Check negative signals such as "do not grill",
"act normally", or "just implement" before activation.

## Invariants

- Suspend act-by-default only for the active task.
- Ask at least one decision or risk question after activation, then stop unless the user
  immediately cancels, says proceed/use your judgment, or already supplied a
  complete Shared Understanding Packet.
- Until the packet is confirmed or the user exits, do not plan, synthesize
  research, choose a design direction, edit, start a goal, or dispatch
  planning/design/execution agents. Read-only fact inspection is allowed only to
  answer discoverable facts before framing the next question.
- If a current-task request names "grill-me" as the desired interaction, treat
  it as explicit. If the user reports that grill behavior is missing from the
  package, route that maintenance task normally.
- Resume normal Teamwork rules after exit; missing required values still ask or
  block under `workflow-contract.md`.

## Loop

1. Inspect available source, docs, config, tests, artifacts, and prior memory for
   factual answers before asking the user.
2. Pick the next unresolved decision branch: scope, acceptance, UX/public
   behavior, data contract, architecture, risk, verification, or stop rule.
3. Ask one question at a time:
   `Question: ... Recommended: ... because ... Alternatives: ...`
4. Record the answer, rejected alternatives, and any explicit deferral.
5. Checkpoint after 5 rounds, material fatigue, or repeated uncertainty: summarize
   decisions and ask whether to continue, proceed, or stop.

## Shared Understanding Packet

Return this before handoff:

```text
Mode: grill
Goal:
Facts checked:
Decisions locked:
Recommended defaults accepted:
Alternatives rejected:
Deferred / user-assumed:
Remaining risks:
Next route: research | plan | debug | execute | review | goal | none
User confirmation:
```

Review treats skipped grill handoff, invented answers, or implementation during
active grill mode as `revise` or `blocked`.
