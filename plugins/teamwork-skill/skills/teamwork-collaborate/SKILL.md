---
name: teamwork-collaborate
description: Use when the user explicitly wants to discuss, brainstorm, compare options, or make a material preference decision, or when unclear intent needs guided clarification; do not use for clear execution or a single discoverable detail.
---

# Teamwork Collaborate

Root owns the conversation. Keep clear work native and activate Collaborate when
the user wants to think together, when an unresolved preference would materially
change the result, or when unclear intent needs guided clarification.

## Method

1. Rebuild the full decision surface first: the final goal, prior work on this
   question, settled constraints and recorded rejections, and the unknowns that
   would change the goal, direction, or acceptance. Start from facts,
   constraints, and the goal. Name the strongest prior work on this question:
   what it already solved and where it stalls. Do not invent a stack from zero.
   Map the discussion from goal to stage to questions with a concise tree or
   list; use Mermaid when the option space needs that structure.
2. A stage is one dependency layer of user-owned decisions. Ask every
   independent, valuable question for that stage together and defer dependents
   later; host UI limits are not Teamwork limits.
3. Develop only meaningfully different options. For each, explain the main
   benefit, cost, assumption, and consequence. Answer three axes, or mark a weak
   axis: relative to priors, is this a new mechanism or packaging; whose pain
   gets lighter; is it a real hard problem for the domain. Practice first:
   unobserved local results are not done. Tests on disk are not verification.
   Practice first forbids claiming an unobserved result; it does not require
   proxy experiments before an authorized real attempt.
4. Resolve discoverable facts directly. Ask the user only for preferences or
   authority that cannot be discovered. Remaining questions that would not
   change the next step are not this stage. Use subagents only for bounded
   evidence gathering or a genuinely independent challenge. Settled user
   constraints must include recorded rejections and decisions, and the
   requested return must not change the topic.
5. When this turn involves experiment scheduling, GPU or other scarce compute, or
   a paper / contribution table slot, follow `references/experiment.md`.
   Otherwise skip Experiment.
6. Recommend a direction when the evidence distinguishes one. Lead with the
   claim, then checkable behavior. Define a new term in one sentence. No
   slogans; do not paper over holes with coinages. Record the user's decision
   and advance to the next dependent stage. Recorded rejections and decisions
   are the mainline; research or a subagent return must not restate them as a
   new question. After research, do not rewrite the question. Quote the user's
   decision or rejection; do not paraphrase it into a new problem. Do not
   reopen settled dimensions; update only what the evidence changed. A fluent
   next step is not convergence. If a new direction is weak on the three axes,
   improve the anchored problem instead of reopening it.
7. End with the decision, unresolved points, and the next authorized action.
   When the direction is decided and the user authorizes execution, the
   discussion ends at that real action; do not open a new evidence gate or a
   new planning door. The next turn on the same subject reads the discussion
   document's current synthesis first when that document exists.

## Persistence

When a listed checkpoint fires, write in the same response cycle. If separate
stable identities each cross a checkpoint, write each to its own path.

Cross-chat memory lives in one Markdown document from `references/discussion.md`
at `docs/teamwork/discussions/<YYYY-MM-DD>-<slug>.md`. Same identity means the
same final goal plus the same subject; reuse that path and name the document you
read. A different subject gets a new path.

Checkpoints: a decision, recommendation, or unresolved question batch that will
change later work. An ordinary next action by itself does not write a document.

Session recall may be used on the next turn only after a write is observed
unavailable or failed, and that recall must be marked as not persisted. A
missing document is not a license to skip a fired checkpoint write.
