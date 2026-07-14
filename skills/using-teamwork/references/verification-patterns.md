# Verification Patterns

Use when a claim needs proof stronger than "tests ran" or an executor summary.
This is a proof lens, not a Teamwork stage.

## Claim Frame

Restate the claim so it can fail:

```text
Claim:
Condition:
Metric / observable:
Threshold:
Surface:
```

For bug, UI, performance, memory, migration, or parity claims, capture baseline
before treatment when practical. Use the same command, input, account, data,
warmup, and environment. If a baseline is impossible, say why and mark the proof
weaker.

## Strength

Report strength separately from the Teamwork verdict:

| Strength | Meaning |
|---|---|
| `live-verified` | Real app, browser, CLI, API, or integration path was exercised. |
| `targeted-test-verified` | A focused test covers the changed path. |
| `build-only` | Build, typecheck, lint, or syntax check only. |
| `blocked` | Environment, credentials, ports, harness, or data prevented proof. |
| `failed` | The check ran and did not prove the claim. |
| `not_applicable` | No runtime or behavioral proof is relevant to this review item. |

Do not round `blocked` up to `build-only`, or `build-only` up to behavioral
proof. For explicit "verify this" requests, return one claim verdict:
`VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE`.

## Evidence Rules

- Verify the real artifact when feasible: runtime behavior, response body,
  generated file, screenshot, trace, profile, database row, or diff.
- Reading code, seeing a green typecheck, or trusting a subagent summary is not
  behavioral verification.
- Map every acceptance criterion to evidence: command, artifact, observation,
  result, and strength.
- Keep an acceptance trace: criterion -> candidate change/no-change rationale
  -> direct evidence -> result -> strength. Preserve a failed, blocked, or
  partial result for that same criterion until new direct evidence changes it.
- For manual smoke, record source, steps, observed state, pass/fail, and any
  artifact path.
- Preserve negative results. `NOT VERIFIED`, `failed`, and `blocked` are useful.

## Internal Record

Keep only the fields needed to support the claim. This record may inform the
user-facing answer, but its exact packet shape is not a presentation requirement.

```text
Verification Strength: live-verified | targeted-test-verified | build-only | blocked | failed
Baseline / Treatment: <baseline evidence> -> <treatment evidence>, or not_applicable
Acceptance Evidence:
- <criterion> -> <command/artifact/observation> -> <pass|fail|partial|not_run>
Confounds:
```
