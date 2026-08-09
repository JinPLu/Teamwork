# {{ title }}

## Candidate, scope, and criteria

{{ stable candidate, protected boundaries, and outcome-based criteria }}

## Outcome Fit

applicability: applicable
reason: {{ supplied requirements and criteria define the outcome to judge for this candidate }}
evidence: {{ candidate content, requirements, acceptance criteria, comparison notes, or unknown if applicable evidence is missing }}
findings: {{ outcome-fit findings ordered by consequence }}

## Engineering Quality

applicability: {{ applicable only when there is an engineering surface; otherwise not applicable with candidate-specific reason }}
reason: {{ why engineering quality matters or why there is no engineering surface }}
evidence: {{ source, diff, configuration, tests, schemas, automation, deployment, or unknown if applicable evidence is missing }}
findings: {{ engineering-quality findings ordered by consequence }}

## Real-Path Evidence

applicability: {{ applicable only for runtime, host, rendered, external, or execution claims; otherwise not applicable with candidate-specific reason }}
reason: {{ why real-path proof is required or why no real-path claim is present }}
evidence: {{ runtime, host, rendered, external, execution evidence, or unknown if applicable evidence is missing }}
findings: {{ real-path findings ordered by consequence }}

## Verdict

{{ Accept, Revise, or Blocked with the reasoning that supports it }}

## Residual Risk and Next Action

{{ remaining uncertainty and the smallest useful next action }}

<!-- Add optional threat or failure model, strict-gate evidence, suggestions, or bounded recheck only when material. Omit empty modules and rename headings when useful. -->
