# Teamwork for Codex

Teamwork adds focused collaboration methods without wrapping ordinary Codex work. Clear requests stay native; a named Skill supplies a method only when its trigger fits.

## Setup

Use the Codex Marketplace package by default. For checkout development:

```bash
./install.sh codex
./install.sh codex --profile cost-first
```

The installer manages Teamwork-owned skills, custom agents, routing support, and the managed global-policy block while preserving unrelated files and settings.

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

Explorer remains an internal read-only local-evidence agent. Challenger is only for strict adversarial challenge. Reviewer handles plan review as well as implementation review.

Collaborate helps select an acceptable direction; Plan begins once that direction is selected. Neither step authorizes implementation.

## Documents and authority

Writer maintains one live document per task when reusable content exists. Skills never ask the model to operate CAS, transactions, hashes, or migration machinery.

Codex tools, permissions, and approvals remain authoritative. Discussing or accepting a plan does not itself authorize edits or external effects. With an exact project root, `teamwork-update` migrates every Teamwork document to the current format; without one it reports project migration as pending.

Pre-7 project documents migrate only through Update. After migration, Codex uses only the new format and has no legacy runtime reader.

## Verify

```bash
./scripts/check-update.sh --readiness
./scripts/validate.sh --full
```

Static readiness cannot prove model routing, external authentication, or live tool behavior. Invoke a Skill explicitly when exact method selection matters.
