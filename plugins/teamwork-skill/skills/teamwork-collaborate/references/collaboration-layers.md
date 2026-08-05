# Collaboration Layers

Use these layers to guide one continuous discussion. Skip settled work, return
to an earlier layer when new ambiguity appears, and combine layers when the
conversation needs it. The layer is never a budget or a mandatory sequence.

## Recognize Ambiguity

Distinguish two kinds of ambiguity before asking:

- **Intent ambiguity:** the user's goal, success criteria, preference, decision
  ownership, or acceptable boundary is unclear. Explain the plausible
  interpretations, recommend a working interpretation, and use native Ask
  Question for the smallest material choice.
- **Knowledge-space ambiguity:** the user cannot yet choose because the relevant
  directions or evidence are not mapped. Run a bounded Research or Explore pass,
  or build a concise option map from known evidence, then return the map and a
  recommendation to the discussion before asking where to focus.

If the intent and next step are already clear, continue without a ritual
question. If a material user-owned choice appears later, return to L1 and ask.

## Choose Ask Or Map First

Ask directly when the decision surface is already understandable and the
answer will change scope, priority, ownership, or the next substantive action.
Before asking, state the current synthesis, distinct viable options or
interpretations, their practical consequence, and a recommendation.

Map first when the user lacks the information needed to choose. Keep the map
bounded to meaningfully different directions, say what remains unknown, and do
not let Research or Explore select the outcome. Present the map to the user and
then ask which branch deserves deeper attention.

Do not ask for discoverable facts or preferences that cannot change the next
step. Do not silently select a consequential preference merely because one
option looks conventional.

## Batch Native Questions

Use the host-native Ask Question surface whenever an answer can materially
change the next step.

- Put necessary independent questions in the same batch when each answer can be
  given without seeing another answer.
- Ask dependent questions in separate batches. Wait for the prerequisite answer
  and do not continue dependent work or answer on the user's behalf.
- Do not impose a workflow-wide question, batch, or round limit. A host limit,
  such as Codex accepting at most three questions in one `request_user_input`
  call, is only a transport limit; send another native batch when needed.
- Reframe after each answer when it changes the option space. Avoid repeating a
  question already answered in the discussion document.

## Move From Global To Detail

Keep the discussion anchored in this order, while skipping what is already
settled:

1. **Overall outcome:** clarify the desired result and how the user will judge
   success.
2. **Boundaries and criteria:** surface constraints, ownership, non-goals, and
   the trade-offs that actually govern the choice.
3. **Directions and evidence:** compare viable approaches, supporting evidence,
   uncertainty, and consequences; recommend a current direction.
4. **Details:** settle only details that still change the chosen result or its
   downstream execution.

Use L2 while expanding and comparing the space. Enter L3 for an explicitly
requested adversarial or stress-test method, or when an active discussion
reveals hard-to-reverse consequences, material value conflict, or conflicting
evidence. L3 challenges the viable directions; it does not take the final choice
away from the user.

## Scenarios

### Broad research direction

User: "Research a new direction for my work."

Treat this as knowledge-space ambiguity. Build a bounded map of relevant
directions, connect each to the user's known work, recommend the most promising
starting point, and use native Ask Question to let the user choose what receives
deeper research. Do not return a broad survey as if it settled the focus.

### Unclear product preference

User: "Make onboarding better."

If speed for experienced users and guidance for first-time users imply different
designs, show that tension and a recommendation, then ask the user-owned success
preference in L1. Continue into L2 after the preference is clear.

### Explicit co-design or brainstorming

User: "Let's design this API together" or "Brainstorm alternatives with me."

Activate Collaborate. Confirm the overall outcome briefly, then use L2 to widen
meaningfully different directions, compare evidence and trade-offs, and ask the
material choices. Actually brainstorm; do not relabel a single recommendation.

### Dependent decisions

User: "First decide whether compatibility is required; that determines the
rollout options."

Ask the compatibility choice first and wait. Update the shared semantic state,
then derive and ask the valid rollout choices in a later native batch.

### Adversarial convergence

User: "Stress-test this choice with independent critics."

Enter L3 and execute the requested adversarial method with real independent
critics when available. Return their disagreement, evidence gaps, and the
current recommendation to the user for the final choice.

### Already selected implementation direction

User: "The design is accepted; write the implementation plan."

Do not reopen the option space merely because the word "plan" appears. Hand the
accepted direction to Plan. Return to Collaborate only if a new material
user-owned choice or unclear intent blocks that plan.
