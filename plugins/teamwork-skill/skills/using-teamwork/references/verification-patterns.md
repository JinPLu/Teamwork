# Verification Patterns

Use only when the user explicitly asks for verification, a comparison claim
needs measurement, or a named protected boundary requires proof stronger than
the real result already observed. This is a proof lens, not a Teamwork stage or
an ordinary build/fix completion requirement.

## Claim Frame

Restate the claim so it can fail:

```text
Claim:
Condition:
Metric / observable:
Threshold:
Surface:
```

Capture baseline/treatment only when the claim is comparative, such as
performance, memory, migration, parity, or regression. Do not create an A/B
exercise for an ordinary fix whose real success path is directly observable.

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
- Map only explicit acceptance criteria and named protected boundaries to direct
  evidence. Do not create a trace packet for ordinary work.
- For manual smoke, record source, steps, observed state, pass/fail, and any
  artifact path.
- Preserve negative results. `NOT VERIFIED`, `failed`, and `blocked` are useful.
- Reuse unchanged evidence. Repeat only after a relevant change, new failure, new
  discriminating hypothesis, or boundary-specific need; stop after the claim is
  decided.

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
