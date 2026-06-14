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

## External Documentation MCP

Context7-class documentation MCPs complement CodeGraph. Use CodeGraph for local
code structure; use the docs MCP for current external library, framework, SDK,
API, or configuration documentation.

When the user or project selects Context7, treat it as an optional docs graph
candidate, not a required Teamwork dependency:

- Source/License or trust note: Upstash Context7 MCP or configured equivalent;
  record repository/plugin source when installation is requested.
- Capability and Role Fit: external documentation lookup, version-specific
  examples, and setup/API usage context; not local source truth, call graph, or
  completion evidence.
- Trigger and No duplicate install check: prefer an already-active Codex
  plugin, connector, or MCP server before adding local CLI/server config.
- Credentials and privacy boundary: send only sanitized library names, library
  IDs, versions, and topic queries. Do not send private source, prompts,
  customer data, secrets, or proprietary implementation details.
- Write Risk and approval point: read-only lookup is allowed when already
  available; MCP/plugin/CLI installation, API key setup, OAuth, private-source
  indexing, policy writes, or repository config changes require explicit user
  approval.
- Smoke Test command or read-only probe: resolve a public library and retrieve
  a small documentation result before relying on it. If no probe is available,
  document `deferred`.
- Decision: `use plugin` when already installed, `adapt` when used only as an
  optional evidence source, `defer` when credentials/privacy/smoke test are
  missing, and never `install` speculatively.
