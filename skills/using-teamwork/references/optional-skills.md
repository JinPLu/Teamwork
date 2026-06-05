# Optional Skills

External skills are tool substrates, not Teamwork roles. Use this gate before
installing or invoking a skill that is not already active.
Skill = reusable workflow or expertise; plugin = installable distribution unit.
For repository-hosted skills, licenses may differ per skill directory.

## Install Gate

1. Use plugin-first: prefer an active Codex plugin or built-in tool over a new
   local skill.
2. No duplicate install when the plugin already covers the capability.
3. Verify source/license or trust note, trigger scope, credential needs,
   write risk, and smoke test before install.
4. Reject broad community packs, write-capable automation loops, or unclear
   licenses until a per-skill audit passes.
5. If credentials or smoke test are unavailable, document `deferred`; do not
   install speculatively.

## Candidate Record

For each candidate, record these current facts before install or use:

- Source/License or trust note
- Capability and Role Fit
- Trigger and No duplicate install check
- Credentials and privacy boundary
- Write Risk and approval point
- Smoke Test command or read-only probe
- Decision: use plugin, install, defer, adapt, or reject

Do not maintain a static external-skill inventory in runtime instructions.
broad community collections require per-skill audit before any candidate record.

## Memory And Docs Graph Candidates

For memory integration or docs graph tools, add:

- Canonical Boundary: recall/search/graph output is candidate context, not
  Teamwork truth.
- Data Scope: repository-only, personal memory, team memory, or external docs.
- Promotion Gate: evidence path, currentness, protected-data check, and
  Memory Delta owner.
- Smoke Test: read-only search/status/API probe before writes or MCP
  registration.

Decision stays `defer` or `adapt` when schema, parser coverage, credentials,
privacy, or write-risk evidence is incomplete.
