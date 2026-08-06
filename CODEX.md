# Teamwork for Codex

Teamwork adds focused collaboration methods without wrapping ordinary Codex work. Clear requests stay native; a named Skill supplies a method only when its trigger fits.

## Setup

Use the Codex Marketplace package by default. For checkout development:

```bash
./install.sh codex
./install.sh codex --profile cost-first
```

The installer manages Teamwork-owned Skills, custom Agents, routing support,
and the Codex managed block rendered from `policy/teamwork-global.md`, while
preserving unrelated files and settings. Readiness reports static installation
and observed policy activation separately. Static profile and
`features.multi_agent` checks do not prove that Codex activated an exact named
role.

Initialize a new project's current-format context with `./install.sh --project-root /path/to/project init-project`.

## Routing

- Local inspection and clear implementation: native Codex.
- Discussion or unformed preference: `teamwork-collaborate`.
- Deep external multi-source work: `teamwork-research`.
- Unknown-cause failure: `teamwork-debug`.
- Clear direction needing a plan: `teamwork-plan`.
- Stable candidate or plan needing review: `teamwork-review`.
- Explicit persistence to a success signal: `teamwork-goal`.
- Project-local context: `teamwork-init`.
- Global Teamwork installation: `teamwork-update`.

Explorer remains an internal read-only local-evidence Agent. Challenger is only
for an explicitly needed adversarial challenge. Reviewer handles plan review as
well as implementation review. Strict Review follows an actual permission,
irreversible user-data, persistent-migration, or changed-public-contract effect,
not the word “release” or subjective risk.

When a Skill requires a named Agent, Codex must expose and honor
`spawn_agent.agent_type`, and the run must retain a live child-start observation
of that exact role. If the current surface cannot do so, Teamwork fails that
Agent-dependent path as unsupported instead of accepting a task name or
self-report. Teamwork does not create, delete, or enable the user's
under-development `multi_agent_v2` setting to manufacture support. Codex CLI
0.144 stable-path support is therefore conditional on the exact role observed
in that run; other Codex surfaces are judged by their own observation.

Collaborate helps select an acceptable direction; Plan begins once that direction is selected. Neither step authorizes implementation.

## Documents and authority

Writer is the sole semantic writer for six typed documents: Discussion,
Research, Debug, Plan, Review, and Report. It writes only when material reusable
content exists and registers each path under the task in
`docs/teamwork/index.json`. Explorer and other leaf Agents return evidence to
Root instead of creating side documents.

Codex tools, permissions, and approvals remain authoritative. Discussing or accepting a plan does not itself authorize edits or external effects. With an exact project root, `teamwork-update` migrates every Teamwork document to the current format; without one it reports project migration as pending.

Older project documents migrate only through Update. Writer performs the
semantic reorganization, migration scripts handle mechanics, and an independent
Reviewer accepts the actual migrated corpus. After migration, Codex uses only
schema v4 and has no legacy runtime reader.

## Verify

```bash
./scripts/check-update.sh --readiness
./scripts/validate.sh --full
```

Structural checks prove layout and schema, installed observations prove host
behavior, and an independent Reviewer proves only the semantic candidate it
actually read. Invoke a Skill explicitly when exact method selection matters.
`check-update.sh --readiness` proves installed state, not exact named-Agent
behavior; use the live release matrix for that claim.
